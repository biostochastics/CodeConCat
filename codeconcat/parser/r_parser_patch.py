# R parser patch for CodeConCat

import logging
logger = logging.getLogger(__name__)

# Original parser function
original_get_language_parser = None

# Patched parser function implementation
def patched_get_language_parser(language, config, parser_type=None):
    # Special handling for R language
    if language == "r":
        logger.info("Using patched R parser selection logic")
        from codeconcat.parser.language_parsers.tree_sitter_r_parser import TreeSitterRParser
        from codeconcat.parser.language_parsers.enhanced_r_parser import EnhancedRParser
        from codeconcat.parser.language_parsers.r_parser import RParser
        
        # Try all parsers in order
        r_parsers = []
        
        # First try tree-sitter if requested
        if not parser_type or parser_type == "tree_sitter":
            try:
                logger.info("Attempting to use Tree-sitter R parser")
                r_parsers.append(TreeSitterRParser())
            except Exception as e:
                logger.warning(f"Tree-sitter R parser not available: {e}")
        
        # Then try enhanced regex
        if not parser_type or parser_type == "enhanced":
            try:
                logger.info("Attempting to use Enhanced R parser")
                r_parsers.append(EnhancedRParser())
            except Exception as e:
                logger.warning(f"Enhanced R parser not available: {e}")
        
        # Finally try standard regex
        if not parser_type or parser_type == "regex":
            try:
                logger.info("Attempting to use Standard R parser")
                r_parsers.append(RParser())
            except Exception as e:
                logger.warning(f"Standard R parser not available: {e}")
        
        # Use first available parser
        for parser in r_parsers:
            logger.info(f"Using R parser: {parser.__class__.__name__}")
            return parser
        
        logger.error("No R parser could be initialized")
        return None
    
    # Use original function for other languages
    return original_get_language_parser(language, config, parser_type)

# Function to apply the patch
def apply_r_parser_patch():
    """Apply the R parser patch to the file_parser module."""
    
    import codeconcat.parser.file_parser as file_parser
    global original_get_language_parser
    
    # Only patch once
    if original_get_language_parser is not None:
        return
        
    # Store original and apply patch
    original_get_language_parser = file_parser.get_language_parser
    file_parser.get_language_parser = patched_get_language_parser
    logger.info("Successfully patched R parser selection logic")
    
    patch_path = os.path.join(
        os.path.dirname(__file__), 
        "codeconcat", 
        "parser", 
        "r_parser_patch.py"
    )
    
    # Create directory if needed
    os.makedirs(os.path.dirname(patch_path), exist_ok=True)
    
    # Write patch file
    with open(patch_path, "w") as f:
        f.write("# R parser patch for CodeConCat\n\n")
        f.write("import logging\nlogger = logging.getLogger(__name__)\n\n")
        f.write("# Original parser function\noriginal_get_language_parser = None\n\n")
        f.write("# Patched parser function implementation\n")
        f.write(inspect.getsource(patched_get_language_parser))
        f.write("\n")
        f.write("# Function to apply the patch\n")
        f.write(inspect.getsource(apply_r_parser_patch))
        f.write("\n")
    
    print(f"Created R parser patch at {patch_path}")
    print("To apply patch, add this import to your code:")
    print("from codeconcat.parser.r_parser_patch import apply_r_parser_patch; apply_r_parser_patch()")

