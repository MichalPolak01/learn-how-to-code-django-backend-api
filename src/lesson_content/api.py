from gettext import translation
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from ninja_extra import Router

from openai import OpenAI
from decouple import config

from lesson.api import add_or_update_student_progress
from lesson.schemas import StudentProgressSchema

from .schemas import CodeEvaluationRequestSchema, CodeEvaluationResponseSchema, LessonIntroductionSchema, LessonQuizSchema, LessonAssignmentSchema, LessonQuizDetailSchema
from learn_how_to_code.schemas import MessageSchema

from .models import LessonIntroduction, LessonQuiz, QuizOption, LessonAssignment
from lesson.models import Lesson

from lesson.api import add_or_update_student_progress
from lesson.schemas import StudentProgressSchema

import helpers
import json

import logging
import traceback
logger = logging.getLogger(__name__)

router = Router()


@router.post(
        '/{lesson_id}/introduction', 
        response={201: LessonIntroductionSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema},
        auth=helpers.auth_required
)
def lesson_introduction(request, lesson_id: int, generate: bool = False, payload: LessonIntroductionSchema = None):
    """Create an introduction for lesson or if param `generate=true` generate the introduction."""
    try:
        lesson = Lesson.objects.get(id=lesson_id)

        if generate:
            introduction_data = generate_introduction(lesson.topic)

            lesson_introduction = LessonIntroduction.objects.create(
                lesson=lesson,
                description=introduction_data['description']
            )
            return 201, lesson_introduction

        else:
            if payload is None:
                return 400, {"message": "Payload is required when not generating the introduction."}

            lesson_introduction = LessonIntroduction.objects.create(
                lesson=lesson,
                description=payload.description
            )
            return 201, lesson_introduction

    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except IntegrityError as e:
        if "unique constraint" in str(e).lower():
            return 400, {"message": "A introduction for this lesson already exists. You cannot create another one."}
        else:
            return 400, {"message": "A database integrity error occurred."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An error occurred while handling the introduction."}
        

# @router.get(
#     '/{lesson_id}/introduction',
#     response={200: LessonIntroductionSchema, 404: MessageSchema, 500: MessageSchema},
#     auth=helpers.auth_required
# )
# def get_lesson_introduction(request, lesson_id: int):
#     """
#     Retrieve the introduction for the specified lesson.
#     """
#     try:
#         lesson = Lesson.objects.get(id=lesson_id)

#         lesson_introduction = LessonIntroduction.objects.filter(lesson=lesson).first()

#         if not lesson_introduction:
#             return 404, {"message": f"Introduction for lesson with id {lesson_id} not found."}

#         return 200, lesson_introduction

#     except Lesson.DoesNotExist:
#         return 404, {"message": f"Lesson with id {lesson_id} not found."}
#     except Exception as e:
#         traceback.print_exc()
#         return 500, {"message": "An error occurred while retrieving the introduction."}


@router.post(
    '/{lesson_id}/quiz',
    response={201: LessonQuizDetailSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema},
    auth=helpers.auth_required
)
def lesson_quiz(request, lesson_id: int, generate: bool = False, payload: LessonQuizSchema = None):
    """Create a quiz for lesson or if `generate=true` generate the quiz."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        if generate:
            quiz_data = generate_quiz(lesson.topic)

            for question_data in quiz_data["questions"]:
                quiz = LessonQuiz.objects.create(
                    lesson=lesson,
                    question=question_data["question"]
                )
                options = []

                for option_data in question_data["options"]:
                    option = QuizOption.objects.create(
                        question=quiz,
                        answer=option_data["option"],
                        is_correct=option_data["is_correct"]
                    )
                    options.append({
                        "id": option.id,
                        "answer": option.answer,
                        "is_correct": option.is_correct
                    })

        else:
            if payload is None:
                return 400, {"message": "Payload is required when not generating the quiz."}

            quiz = LessonQuiz.objects.create(
                lesson=lesson,
                question=payload.question
            )

            options = []
            for option_data in payload.answers:
                option = QuizOption.objects.create(
                    question=quiz,
                    answer=option_data.answer,
                    is_correct=option_data.is_correct
                )
                options.append({
                    "id": option.id,
                    "answer": option.answer,
                    "is_correct": option.is_correct
                })

        return 201, {
            "id": quiz.id,
            "question": quiz.question,
            "answers": options
        }

    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An error occurred while handling the quiz."}
   

@router.post('/{lesson_id}/assignment', response={201: LessonAssignmentSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def lesson_assignment(request, lesson_id: int, generate: bool = False, payload: LessonAssignmentSchema = None):
    """Create an assignment for lesson or if `generate=true` generate the assignment."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        if generate:
            lesson = Lesson.objects.get(id=lesson_id)

            assignment_data = generate_assignment(lesson.topic)

            lesson_assignment= LessonAssignment.objects.create(
                lesson=lesson,
                instructions=assignment_data['instruction']
            )

        else:
            lesson_assignment= LessonAssignment.objects.create(
                lesson=lesson,
                instructions=payload.instructions
            )
        
        return 201, lesson_assignment
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except IntegrityError as e:
        if "unique constraint" in str(e).lower():
            return 400, {"message": "A assignment for this lesson already exists. You cannot create another one."}
        else:
            return 400, {"message": "A database integrity error occurred."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An error occurred while creating the assignment."}
    
    
    
def generate_introduction(lesson_name: str, language: str = "polish"):
    try:
        client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an educational content creator skilled in web formatting. "
                        f"Respond in JSON format with a single key 'description' containing the HTML-formatted content as plain text. "
                        f"Respond only with the JSON object, without any extra formatting. Use {language} for the response."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Create a detailed, structured description for a lesson on '{lesson_name}'. "
                        "The description should start with a short paragraph in <p> tags, have a main heading in <h1>, "
                        "key sections with <h2> subheadings, and code examples in <pre><code> blocks if applicable. "
                        "Conclude with a brief summary. Ensure all HTML tags are used semantically and the entire response is inside the 'description' key."
                    )
                }
            ]
        )
        result = response.choices[0].message.content

        try:
            parsed_result = json.loads(result)
            return parsed_result
        except json.JSONDecodeError as e:
            return [{"error": "Model did not return valid JSON format", "response": result}]
    except Exception as e:
        raise


def generate_quiz(lesson_name: str, language: str = "polish") -> dict:
    try:
        client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a quiz generator. Respond in JSON format with a single key 'questions', containing a list of questions. "
                        f"Each question should have the keys 'question' (the main quiz question) and 'options' (a list of answer options). "
                        f"Each item in 'options' should be an object with 'option' (text of the answer) and 'is_correct' (boolean indicating if this option is correct). "
                        f"Use {language} for all content."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate a multiple-choice quiz for a lesson on '{lesson_name}' with exactly 3 questions. "
                        "The response should be a JSON object with the following structure:"
                        "{"
                        "  'questions': ["
                        "    {"
                        "      'question': 'The main quiz question as a string.',"
                        "      'options': ["
                        "        {'option': 'Answer text 1', 'is_correct': true or false},"
                        "        {'option': 'Answer text 2', 'is_correct': true or false},"
                        "        {'option': 'Answer text 3', 'is_correct': true or false},"
                        "        {'option': 'Answer text 4', 'is_correct': true or false}"
                        "      ]"
                        "    }"
                        "  ]"
                        "}"
                        "Ensure the JSON structure is valid, follows this format exactly, and contains no extra text or explanations."
                    )
                }
            ]
        )
        result = response.choices[0].message.content
        
        try:
            parsed_result = json.loads(result)
            return parsed_result
        except json.JSONDecodeError as e:
            return [{"error": "Model did not return valid JSON format", "response": result}]
    except Exception as e:
        raise


def generate_assignment(lesson_name: str, language: str = "polish"):
    try:
        client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an educational content creator skilled in creating structured assignments for students. "
                        f"Respond only in JSON format with a single key 'instruction', containing the assignment instructions as plain HTML content. "
                        f"Ensure that all instructions are clear, detailed, and well-formatted. Respond only with the JSON object, without any extra formatting or explanations. Use {language} for the response."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Create a detailed assignment instruction for a lesson on '{lesson_name}'. "
                        "The instruction should:\n"
                        "- Begin with a brief introduction to the assignment in <p> tags.\n"
                        "- Include a main heading for the assignment using <h1> tags.\n"
                        "- Provide a step-by-step guide, with each step wrapped in <li> tags inside an <ol> tag.\n"
                        "- If relevant, include example code snippets within <pre><code> tags to guide the student.\n"
                        "- Conclude with tips or advice in <em> tags, if necessary.\n\n"
                        "Ensure that all HTML tags are semantically appropriate and the entire response is contained in the 'instruction' key."
                    )
                }
            ]
        )
        result = response.choices[0].message.content

        try:
            parsed_result = json.loads(result)
            return parsed_result
        except json.JSONDecodeError as e:
            return [{"error": "Model did not return valid JSON format", "response": result}]
    except Exception as e:
        raise


@router.post(
    "/assignments/evaluate", 
    response={200: CodeEvaluationResponseSchema, 400: MessageSchema, 404: MessageSchema, 500: MessageSchema}, 
    auth=helpers.auth_required
)
def evaluate_assignment(request, data: CodeEvaluationRequestSchema):
    """
    Endpoint to evaluate a user's code for a specific lesson's assignment.
    """
    try:
        lesson = get_object_or_404(Lesson, id=data.lesson_id)
        assignment = get_object_or_404(LessonAssignment, lesson=lesson)
        assignment_instructions = assignment.instructions

        evaluation_result = evaluate_code_response(
            assignment_instructions=assignment_instructions,
            user_code=data.user_code,
        )

        student_progress_data = StudentProgressSchema(
            lesson_id=lesson.id,
            assignment_score=evaluation_result.assignment_score,
        )

        progress_status, progress_response = add_or_update_student_progress(
            request=request,
            data=student_progress_data,
        )

        if progress_status not in [200, 201]:
            return 400, {
                "message": "Evaluation completed, but failed to update student progress.",
                "evaluation": evaluation_result.dict(),
                "progress_response": progress_response,
            }

        return 200, evaluation_result

    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {data.lesson_id} not found."}
    except LessonAssignment.DoesNotExist:
        return 404, {"message": f"No assignment found for lesson with id {data.lesson_id}."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": f"An unexpected error occurred: {str(e)}"}


def evaluate_code_response(
    assignment_instructions: str,
    user_code: str,
    language: str = "polish"
) -> CodeEvaluationResponseSchema:
    """
    Evaluates a user's code against assignment instructions using AI.
    """

    client = OpenAI(api_key=config('OPENAI_API_KEY', cast=str))

    try:
        completion = client.beta.chat.completions.parse(
            model=config("OPEN_API_MODEL", cast=str),
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an AI programming assistant. Your task is to evaluate a user's code submission for a programming assignment. "
                        f"Provide constructive feedback and a score based on correctness, optimization, and readability. "
                        f"Ignore minor issues that do not affect the program's correctness or execution, such as variable names, minor typos in comments, or formatting inconsistencies, unless explicitly requested in the assignment. "
                        f"Only focus on true coding errors (e.g., syntax errors, logical flaws, or deviations from the instructions). "
                        f"If the code functions correctly but is not optimized, assign a score of approximately 75-80. "
                        f"Respond in JSON format with the following keys:\n"
                        f"1. 'assignment_score': A float between 0-100, where:\n"
                        f"   - 100 is perfect, fully correct, optimized, and clean code.\n"
                        f"   - Over 70 for correct but not optimized code.\n"
                        f"   - Below 50 is for code with significant errors or incomplete functionality.\n"
                        f"2. 'message': Constructive feedback formatted as a valid HTML string, suitable for display on a web page. "
                        f"Use headings and bullet points for clarity.\n"
                        f"Language: {language}."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Assignment Instructions:\n\n{assignment_instructions}\n\n"
                        f"User Code:\n\n{user_code}\n\n"
                        f"Evaluate the code, provide constructive feedback in HTML, and assign a score."
                    )
                }
            ],
            response_format=CodeEvaluationResponseSchema,
        )

        parsed_response = completion.choices[0].message.parsed

        return parsed_response

    except Exception as e:
        raise Exception(f"An error occurred while evaluating the code: {str(e)}")
