from ninja_extra import Router

from openai import OpenAI
from decouple import config

from module.schemas import ModuleDetailSchema
from learn_how_to_code.schemas import MessageSchema

from module.models import Module

import helpers
import json

import logging
import traceback
logger = logging.getLogger(__name__)

router = Router()