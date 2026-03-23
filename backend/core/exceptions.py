from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    DRF의 기본 예외 처리기를 래핑하여, 모든 에러 응답을 표준 포맷으로 통일합니다.
    """
    # 1. DRF가 기본적으로 처리한 결과를 먼저 받습니다.
    response = exception_handler(exc, context)

    # 2. 예외 처리가 된 경우 (response가 None이 아님)
    if response is not None:
        custom_data = {
            "success": False,
            "code": "UNKNOWN_ERROR",
            "message": "An error occurred.",
            "data": None,  # detail error info
        }

        # 에러 코드 및 메시지 매핑 로직
        if isinstance(exc, APIException):
            custom_data["code"] = (
                exc.default_code.upper()
                if hasattr(exc, "default_code")
                else "API_ERROR"
            )

            # detail이 문자열이면 message로, 리스트/딕셔너리며 data로
            if isinstance(response.data, dict) and "detail" in response.data:
                custom_data["message"] = response.data["detail"]
                custom_data["data"] = None  # detail외에 다른게 없다고 가정
            elif isinstance(response.data, dict):
                custom_data["message"] = "Validation failed."
                custom_data["code"] = "VALIDATION_ERROR"
                custom_data["data"] = response.data
            elif isinstance(response.data, list):
                custom_data["message"] = response.data[0]
                custom_data["data"] = response.data
            else:
                custom_data["message"] = str(response.data)

        response.data = custom_data

    return response


class ApplicationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Application logic error."
    default_code = "APPLICATION_ERROR"

    def __init__(self, detail=None, code=None):
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.default_code = code
        super().__init__(detail, code)
