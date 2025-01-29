from ninja.errors import ValidationError

def validation_error_handler(request, exc: ValidationError):
    print("Global Validation Error Details:", exc.errors)
    return 422, {"message": "Validation error occurred", "errors": exc.errors}
