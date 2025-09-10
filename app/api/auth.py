"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, CurrentUser
from app.schemas.auth import (
    UserLogin,
    UserRegister,
    UserCreate,
    Token,
    TokenPair,
    RefreshTokenRequest,
    UserResponse,
    UserWithCompany,
    CompanyResponse,
    PasswordValidationRequest,
    PasswordValidationResponse
)
from app.services.auth import AuthService
from app.core.logging import get_logger
# from app.core.rate_limiting import rate_limit, RateLimitType
from app.core.auth_rate_limiting import get_auth_rate_limiter, AuthAttemptResult
from app.core.password_policy import PasswordPolicy
from fastapi import Request

logger = get_logger(__name__)
router = APIRouter()


@router.post("/login", response_model=TokenPair)
# @rate_limit(RateLimitType.AUTH, per_user=False)  # Rate limit by IP for login attempts - temporarily disabled
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access and refresh tokens.

    Args:
        user_credentials: User login credentials
        request: FastAPI request object
        db: Database session

    Returns:
        JWT access and refresh tokens

    Raises:
        HTTPException: If authentication fails or rate limited
    """
    # Check enhanced auth rate limiting
    auth_rate_limiter = await get_auth_rate_limiter()
    is_allowed, rate_info = await auth_rate_limiter.check_auth_rate_limit(
        request=request,
        email=user_credentials.email
    )

    if not is_allowed:
        # Record the rate-limited attempt
        await auth_rate_limiter.record_auth_attempt(
            request=request,
            email=user_credentials.email,
            result=AuthAttemptResult.RATE_LIMITED
        )

        logger.warning(
            "Login rate limited",
            email=user_credentials.email,
            reason=rate_info.get("lockout_reason", "Rate limit exceeded")
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Too many login attempts. Please try again later.",
                "error_code": "AUTH_RATE_LIMITED",
                "reason": rate_info.get("lockout_reason"),
                "lockout_until": rate_info.get("ip_limit", {}).get("lockout_until") or
                               rate_info.get("email_limit", {}).get("lockout_until")
            },
            headers={"Retry-After": "300"}  # Suggest retry after 5 minutes
        )

    auth_service = AuthService(db)

    # Authenticate user
    user = auth_service.authenticate_user(
        email=user_credentials.email,
        password=user_credentials.password
    )

    if not user:
        # Record failed authentication attempt
        await auth_rate_limiter.record_auth_attempt(
            request=request,
            email=user_credentials.email,
            result=AuthAttemptResult.FAILED_CREDENTIALS
        )

        logger.warning("Login failed", email=user_credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Record successful authentication
    await auth_rate_limiter.record_auth_attempt(
        request=request,
        email=user_credentials.email,
        result=AuthAttemptResult.SUCCESS,
        user_id=str(user.id)
    )

    # Create token pair
    access_token, refresh_token, access_expires_in, refresh_expires_in = auth_service.create_token_pair_for_user(user)

    logger.info("User logged in successfully", email=user.email, user_id=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "access_expires_in": access_expires_in,
        "refresh_expires_in": refresh_expires_in
    }


@router.post("/register", response_model=TokenPair)
# @rate_limit(RateLimitType.AUTH, per_user=False)  # Rate limit by IP for registration attempts
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user and company.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        JWT access and refresh tokens for the new user
    """
    auth_service = AuthService(db)

    # Register user and company
    user, company = auth_service.register_user_and_company(user_data)

    # Create token pair for the new user
    access_token, refresh_token, access_expires_in, refresh_expires_in = auth_service.create_token_pair_for_user(user)

    logger.info(
        "User registered successfully",
        email=user.email,
        user_id=str(user.id),
        company_id=str(company.id)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "access_expires_in": access_expires_in,
        "refresh_expires_in": refresh_expires_in
    }


@router.post("/refresh", response_model=Token)
# @rate_limit(RateLimitType.STANDARD, per_user=True)  # Rate limit by user for token refresh
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Args:
        refresh_request: Refresh token request
        db: Database session

    Returns:
        New JWT access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    auth_service = AuthService(db)

    try:
        # Create new access token using refresh token
        access_token, expires_in = auth_service.refresh_access_token(refresh_request.refresh_token)

        logger.info("Access token refreshed successfully")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in
        }

    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserWithCompany)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information with company details
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "company": {
            "id": current_user.company.id,
            "name": current_user.company.name,
            "company_type": current_user.company.company_type,
            "email": current_user.company.email
        }
    }


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Create a new user (admin only).
    
    Args:
        user_data: User creation data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Created user information
    """
    auth_service = AuthService(db)
    
    user = auth_service.create_user(user_data)
    
    logger.info(
        "User created by admin", 
        created_user_email=user.email,
        created_user_id=str(user.id),
        admin_user_id=str(current_user.id)
    )
    
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Get user by ID (admin only).
    
    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    auth_service = AuthService(db)
    
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    """
    Deactivate a user (admin only).
    
    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    auth_service = AuthService(db)
    
    success = auth_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(
        "User deactivated by admin", 
        deactivated_user_id=user_id,
        admin_user_id=str(current_user.id)
    )
    
    return {"message": "User deactivated successfully"}


@router.post("/validate-password", response_model=PasswordValidationResponse)
async def validate_password(
    validation_request: PasswordValidationRequest
):
    """
    Validate password strength and policy compliance.

    Args:
        validation_request: Password validation request

    Returns:
        Password validation result with strength score and suggestions
    """
    password_policy = PasswordPolicy()

    # Prepare user info for validation
    user_info = {}
    if validation_request.email:
        user_info["email"] = validation_request.email
    if validation_request.first_name:
        user_info["first_name"] = validation_request.first_name
    if validation_request.last_name:
        user_info["last_name"] = validation_request.last_name
    if validation_request.company_name:
        user_info["company_name"] = validation_request.company_name

    # Validate password
    result = password_policy.validate_password(validation_request.password, user_info)

    logger.info(
        "Password validation performed",
        strength=result.strength.value,
        score=result.score,
        is_valid=result.is_valid
    )

    return PasswordValidationResponse(
        is_valid=result.is_valid,
        strength=result.strength.value,
        score=result.score,
        errors=result.errors,
        warnings=result.warnings,
        suggestions=result.suggestions
    )
