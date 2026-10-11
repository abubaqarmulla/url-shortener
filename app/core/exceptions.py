from fastapi import Request
from fastapi.responses import JSONResponse


class URLNotFoundException(Exception):
    pass


class UnauthorizedException(Exception):
    pass


class ResourceNotFoundException(Exception):
    pass


async def url_not_found_handler(
    request: Request,
    exception: URLNotFoundException,
):
    return JSONResponse(
        status_code=404,
        content={
            "error": "URL_NOT_FOUND",
            "message": "The requested short URL does not exist.",
        },
    )


async def unauthorized_handler(
    request: Request,
    exception: UnauthorizedException,
):
    return JSONResponse(
        status_code=401,
        content={
            "error": "UNAUTHORIZED",
            "message": "Authentication is required.",
        },
    )


async def resource_not_found_handler(
    request: Request,
    exception: ResourceNotFoundException,
):
    return JSONResponse(
        status_code=404,
        content={
            "error": "RESOURCE_NOT_FOUND",
            "message": "The requested resource was not found.",
        },
    )
