from ninja_extra import Router

from openai import OpenAI
from decouple import config

from .schemas import LessonDescriptionSchema, LessonQuizSchema, LessonAssignmentSchema
from module.schemas import ModuleDetailSchema
from learn_how_to_code.schemas import MessageSchema

from .models import LessonDescription, LessonQuiz, QuizOption, LessonAssigment
from lesson.models import Lesson

import helpers
import json

import logging
import traceback
logger = logging.getLogger(__name__)

router = Router()

@router.post('/lessons/{lesson_id}/description/generate', response={201: LessonDescriptionSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lesson_description(request, lesson_id: int):
    """Generates a description for a specific lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        description_data = generate_description(lesson.name)

        lesson_description = LessonDescription.objects.create(
            lesson=lesson,
            description=description_data['description']
        )
        
        return 201, lesson_description
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        return 500, {"message": "An error occurred while generating the description."}
    

@router.post('/lessons/{lesson_id}/description', response={201: LessonDescriptionSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lesson_description(request, payload: LessonDescriptionSchema, lesson_id: int):
    """Allows a teacher to manually create a description for a lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        lesson_description = LessonDescription.objects.create(
            lesson=lesson,
            description=payload.description
        )
        
        return 201, lesson_description
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        return 500, {"message": "An error occurred while creating the description."}
    

def generate_description(lesson_name: str, language: str = "polish"):
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


@router.post('/lessons/{lesson_id}/quiz/generate', response={201: list[LessonQuizSchema], 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lesson_quiz(request, lesson_id: int):
    """Generates a quiz for a lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)
        quiz_data = generate_quiz(lesson.name)

        if not isinstance(quiz_data, dict) or "questions" not in quiz_data:
            print("Debug: quiz_data ma nieprawidłowy format:", quiz_data)
            return 500, {"message": "Generated quiz format is invalid"}
        
        questions = []
        for question_data in quiz_data["questions"]:
            quiz = LessonQuiz.objects.create(
                lesson=lesson,
                question=question_data['question']
            )
            for option_data in question_data['options']:
                QuizOption.objects.create(
                    quiz=quiz,
                    option=option_data['option'],
                    is_correct=option_data['is_correct']
                )
            questions.append({
                "question": quiz.question,
                "options": [{"option": opt.option, "is_correct": opt.is_correct} for opt in quiz.options.all()]
            })

        return 201, questions
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An error occurred while generating the quiz."}
    

@router.post('/lessons/{lesson_id}/quiz', response={201: LessonQuizSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lesson_quiz(request, payload: LessonQuizSchema, lesson_id: int):
    """Allows a teacher to manually create a quiz for a lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        quiz = LessonQuiz.objects.create(
            lesson=lesson,
            question=payload.question
        )

        for option_data in payload.options:
            QuizOption.objects.create(
                quiz=quiz,
                option=option_data.option,
                is_correct=option_data.is_correct
            )
        
        return 201, {"question": quiz.question, "options": quiz.options.all()}
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        return 500, {"message": "An error occurred while creating the quiz."}
    

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



@router.post('/lessons/{lesson_id}/assignment/generate', response={201: LessonAssignmentSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lesson_assignment(request, lesson_id: int):
    """Generates an assignment for a specific lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        assignment_data = generate_assignment(lesson.name)

        lesson_assignment= LessonAssigment.objects.create(
            lesson=lesson,
            instructions=assignment_data['instruction']
        )
        
        return 201, lesson_assignment
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An error occurred while generating the assignment."}
    

@router.post('/lessons/{lesson_id}/assignment', response={201: LessonAssignmentSchema, 404: MessageSchema, 500: MessageSchema}, auth=helpers.auth_required)
def generate_lesson_assignment(request, payload: LessonAssignmentSchema, lesson_id: int):
    """Allows a teacher to manually create a assignment for a lesson."""

    try:
        lesson = Lesson.objects.get(id=lesson_id)

        lesson_assignment= LessonAssigment.objects.create(
            lesson=lesson,
            instructions=payload.instructions
        )
        
        return 201, lesson_assignment
    except Lesson.DoesNotExist:
        return 404, {"message": f"Lesson with id {lesson_id} not found."}
    except Exception as e:
        traceback.print_exc()
        return 500, {"message": "An error occurred while creating the assignment."}
    

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