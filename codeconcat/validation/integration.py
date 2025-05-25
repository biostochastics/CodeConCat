"""
Integration helpers for the validation modules.

This module provides helper functions to integrate validation throughout the CodeConCat application.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import logging
from ..base_types import CodeConCatConfig, ParsedFileData
from ..errors import ValidationError, ConfigurationError
from . import InputValidator as IV # Alias to avoid potential naming conflicts locally, though 'InputValidator' should be fine
from .schema_validation import validate_against_schema
from .security import security_validator
from .semgrep_validator import semgrep_validator
from .setup_semgrep import install_semgrep, install_apiiro_ruleset

logger = logging.getLogger(__name__)

def validate_input_files(files_to_process: List[ParsedFileData], config: CodeConCatConfig) -> List[ParsedFileData]:
    """
    Validate a list of input files for processing.
    
    Performs multiple validation checks:
    1. File existence and accessibility
    2. File size limits
    3. File extension validation
    4. Security checks for suspicious content
    
    Args:
        files_to_process: List of ParsedFileData objects to validate
        config: The application configuration
        
    Returns:
        List of validated ParsedFileData objects
        
    Raises:
        ValidationError: If validation fails for any file
    """
    validated_files = []
    validation_errors = []
    logger_int = logging.getLogger(__name__)
    
    for file_data in files_to_process:
        try:
            file_path = file_data.file_path
            
            # Skip files with no content
            if file_data.content is None:
                continue
                
            # 1. Basic path validation
            logger_int.debug(f"[validate_input_files] config.target_path: {config.target_path}")
            validation_base_dir = Path(config.target_path).resolve() if config.target_path else None
            logger_int.debug(f"[validate_input_files] validation_base_dir for '{file_path}': {validation_base_dir}")
            IV.validate_file_path(file_path, base_dir=validation_base_dir)
            
            # 2. File size validation
            max_size = getattr(config, "max_file_size", 10 * 1024 * 1024)  # Default 10MB
            IV.validate_file_size(file_path, max_size, base_dir=validation_base_dir)
            
            # 3. If strict validation is enabled, perform more checks
            if getattr(config, "strict_validation", False) or config.enable_security_scanning:
                # Check for suspicious content with standard security checks
                use_semgrep = getattr(config, "enable_semgrep", False)
                suspicious_patterns = security_validator.check_for_suspicious_content(
                    file_path, use_semgrep=use_semgrep
                )
                
                if suspicious_patterns and hasattr(config, "strict_security") and config.strict_security:
                    # In strict security mode, files with suspicious content are rejected
                    pattern_names = [p.get("name", str(p)) for p in suspicious_patterns if isinstance(p, dict)]
                    pattern_str = ", ".join(pattern_names)
                    raise ValidationError(
                        f"Suspicious content detected in {file_path}: {pattern_str}",
                        field="file_content"
                    )
                elif suspicious_patterns:
                    # Otherwise, just log a warning
                    pattern_names = [p.get("name", str(p)) for p in suspicious_patterns if isinstance(p, dict)]
                    pattern_str = ", ".join(pattern_names)
                    logger.warning(
                        f"Suspicious content patterns detected in {file_path}: {pattern_str}"
                    )
            
            # File passed validation
            validated_files.append(file_data)
            
        except ValidationError as e:
            # Log validation error and continue with other files
            logger.warning(f"Validation error for file {file_data.file_path}: {e}")
            validation_errors.append((file_data.file_path, str(e)))
            continue
    
    # If validation errors occurred, log summary
    if validation_errors:
        logger.warning(f"Validation failed for {len(validation_errors)} files")
        for path, error in validation_errors:
            logger.debug(f"  - {path}: {error}")
        
        # In strict_security mode, fail if any security issues were found
        if hasattr(config, "strict_security") and config.strict_security:
            # Check if any of the errors are security-related
            security_errors = [
                (path, error) for path, error in validation_errors 
                if "suspicious content" in error.lower() or "security" in error.lower()
            ]
            if security_errors:
                raise ValidationError(
                    f"Security validation failed for {len(security_errors)} files with strict_security enabled. "
                    f"First error: {security_errors[0][1]}",
                    field="file_security"
                )
    
    return validated_files

def validate_config_values(config: Union[Dict[str, Any], CodeConCatConfig]) -> bool:
    """
    Validate configuration values against the schema.
    
    Args:
        config: Configuration dictionary or CodeConCatConfig object
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValidationError: If configuration is invalid
        ConfigurationError: If configuration conversion fails
    """
    # Convert CodeConCatConfig to dict if needed
    if not isinstance(config, dict):
        try:
            config_data = config
            config_dict = config_data.model_dump(exclude_none=True)
        except AttributeError:
            try:
                # Try to convert to dict using __dict__
                config_dict = vars(config)
            except Exception as e:
                raise ConfigurationError(f"Failed to convert configuration to dictionary: {e}")
    else:
        config_dict = config
    
    # Validate against schema
    try:
        validate_against_schema(config_dict, "config", context="configuration")
        return True
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed: {e}")

def sanitize_output(content: str, sensitive_data: bool = True) -> str:
    """
    Sanitize output content to remove sensitive data.
    
    Args:
        content: Content to sanitize
        sensitive_data: Whether to remove sensitive data like secrets and API keys
        
    Returns:
        Sanitized content
    """
    return security_validator.sanitize_content(content)

def setup_semgrep(config: CodeConCatConfig) -> bool:
    """
    Set up Semgrep and the Apiiro ruleset if requested.
    
    Args:
        config: The application configuration
        
    Returns:
        True if Semgrep is available (either already installed or newly installed)
    """
    # Check if semgrep is already available
    if semgrep_validator.is_available():
        logger.info("Semgrep is already installed")
        
        # Update the ruleset path if specified
        if config.semgrep_ruleset:
            semgrep_validator.ruleset_path = config.semgrep_ruleset
            logger.info(f"Using custom Semgrep ruleset: {config.semgrep_ruleset}")
        
        return True
        
    # Install Semgrep if requested
    if config.install_semgrep:
        logger.info("Installing Semgrep...")
        if install_semgrep():
            import shutil
            # Refresh the validator's semgrep path
            semgrep_validator.semgrep_path = shutil.which("semgrep")
            
            # Install the Apiiro ruleset if no custom ruleset is specified
            if not config.semgrep_ruleset:
                try:
                    ruleset_path = install_apiiro_ruleset()
                    semgrep_validator.ruleset_path = ruleset_path
                    logger.info(f"Installed Apiiro ruleset to {ruleset_path}")
                except ValidationError as e:
                    logger.warning(f"Failed to install Apiiro ruleset: {e}")
            else:
                # Use the custom ruleset
                semgrep_validator.ruleset_path = config.semgrep_ruleset
                logger.info(f"Using custom Semgrep ruleset: {config.semgrep_ruleset}")
                
            return True
        else:
            logger.warning("Failed to install Semgrep. Security scanning will be limited.")
            return False
    
    # Semgrep not available and not requested to be installed
    if config.enable_semgrep:
        logger.warning("Semgrep requested but not installed. Run with --install-semgrep to install it.")
    
    return False

def verify_file_signatures(files_to_process: List[ParsedFileData]) -> Dict[str, str]:
    """
    Verify file signatures (content types) to ensure they match expectations.
    
    Args:
        files_to_process: List of ParsedFileData objects to verify
        
    Returns:
        Dictionary mapping file paths to detected content types
        
    Raises:
        ValidationError: If a file's content type doesn't match its extension
    """
    results = {}
    
    for file_data in files_to_process:
        file_path = file_data.file_path
        path = Path(file_path)
        
        # Skip files with no content
        if file_data.content is None:
            continue
        
        # Check if it's a binary file
        is_binary = security_validator.is_binary_file(file_path)
        
        if is_binary:
            # Some code files should never be binary
            code_extensions = {'.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.md'}
            if path.suffix.lower() in code_extensions:
                raise ValidationError(
                    f"File {file_path} has a code extension but appears to be binary",
                    field="file_type"
                )
            
            results[file_path] = "binary"
        else:
            results[file_path] = "text"
    
    return results
