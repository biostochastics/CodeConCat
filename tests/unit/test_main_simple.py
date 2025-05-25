"""Simple but comprehensive tests for the main module."""

import pytest
import sys
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch, call, mock_open
import argparse

from codeconcat.main import (
    configure_logging,
    build_parser,
    create_default_config,
    _create_basic_config,
    generate_folder_tree,
    run_codeconcat,
    run_codeconcat_in_memory,
    _write_output_files,
    main,
    cli_entry_point,
    FileProcessingError,
)
from codeconcat.base_types import CodeConCatConfig


class TestConfigureLogging:
    """Test suite for configure_logging function."""

    def test_configure_logging_default(self):
        """Test default logging configuration."""
        with patch('logging.basicConfig') as mock_basic_config:
            configure_logging()
            mock_basic_config.assert_called_once()
            args = mock_basic_config.call_args[1]
            assert args['level'] == logging.WARNING

    def test_configure_logging_debug(self):
        """Test debug mode logging configuration."""
        with patch('logging.basicConfig') as mock_basic_config:
            configure_logging(debug=True)
            mock_basic_config.assert_called_once()
            args = mock_basic_config.call_args[1]
            assert args['level'] == logging.DEBUG

    def test_configure_logging_quiet(self):
        """Test quiet mode logging configuration."""
        with patch('logging.basicConfig') as mock_basic_config:
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                configure_logging(quiet=True)
                
                mock_basic_config.assert_called_once()
                args = mock_basic_config.call_args[1]
                assert args['level'] == logging.ERROR


class TestBuildParser:
    """Test suite for build_parser function."""

    def test_build_parser_creates_parser(self):
        """Test that build_parser creates an ArgumentParser."""
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_build_parser_has_required_arguments(self):
        """Test parser has required arguments."""
        parser = build_parser()
        
        # Test with minimal args
        args = parser.parse_args(['test_path'])
        assert args.target_path == 'test_path'

    def test_build_parser_optional_arguments(self):
        """Test parser optional arguments."""
        parser = build_parser()
        
        # Test various optional args
        args = parser.parse_args([
            'test_path',
            '-o', 'output.md',
            '-f', 'json',
            '--debug',
            '--quiet'
        ])
        
        assert args.target_path == 'test_path'
        assert args.output == 'output.md'
        assert args.format == 'json'
        assert args.debug is True
        assert args.quiet is True


class TestCreateDefaultConfig:
    """Test suite for create_default_config function."""

    @patch('codeconcat.config.interactive_config.run_interactive_setup')
    def test_create_default_config_interactive(self, mock_interactive_setup):
        """Test creating default config in interactive mode."""
        mock_interactive_setup.return_value = True
        
        create_default_config(interactive=True)
        
        mock_interactive_setup.assert_called_once()

    @patch('codeconcat.main._create_basic_config')
    def test_create_default_config_non_interactive(self, mock_create_basic):
        """Test creating default config in non-interactive mode."""
        create_default_config(interactive=False)
        
        mock_create_basic.assert_called_once()


class TestCreateBasicConfig:
    """Test suite for _create_basic_config function."""

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_basic_config(self, mock_file, mock_exists):
        """Test creating basic config file."""
        mock_exists.return_value = False
        _create_basic_config()
        
        # Should open the config file for writing
        mock_file.assert_called_with('.codeconcat.yml', 'w')
        # Check that some content was written
        assert mock_file().write.called or mock_file().__enter__().write.called


class TestGenerateFolderTree:
    """Test suite for generate_folder_tree function."""

    def test_generate_folder_tree_simple(self):
        """Test generating folder tree for simple structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test structure
            Path(tmpdir, 'dir1').mkdir()
            Path(tmpdir, 'dir1/file1.py').touch()
            Path(tmpdir, 'file2.js').touch()  # Changed to .js to avoid doc_extensions
            
            config = MagicMock(spec=CodeConCatConfig)
            config.exclude_patterns = []
            config.use_gitignore = False
            config.use_default_excludes = False
            config.exclude_paths = []
            config.include_paths = []
            config.doc_extensions = ['.md', '.rst', '.txt']
            config.include_languages = None
            config.exclude_languages = None
            config.verbose = False
            config.target_path = tmpdir
            config.parser_engine = 'tree_sitter'
            
            tree = generate_folder_tree(tmpdir, config)
            
            assert 'dir1' in tree
            assert 'file1.py' in tree
            assert 'file2.js' in tree  # Changed to match the new file

    def test_generate_folder_tree_with_exclusions(self):
        """Test folder tree with exclusions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test structure
            Path(tmpdir, 'src').mkdir()
            Path(tmpdir, 'src/main.py').touch()
            Path(tmpdir, 'node_modules').mkdir()
            Path(tmpdir, 'node_modules/package.json').touch()
            
            config = MagicMock(spec=CodeConCatConfig)
            config.exclude_patterns = ['node_modules']
            config.use_gitignore = False
            config.use_default_excludes = True
            config.exclude_paths = ['node_modules']
            config.include_paths = []
            config.doc_extensions = ['.md', '.rst', '.txt']
            config.include_languages = None
            config.exclude_languages = None
            config.verbose = False
            config.target_path = tmpdir
            config.parser_engine = 'tree_sitter'
            
            tree = generate_folder_tree(tmpdir, config)
            
            assert 'src' in tree
            assert 'main.py' in tree
            assert 'node_modules' not in tree


class TestRunCodeConcat:
    """Test suite for run_codeconcat function."""

    @patch('codeconcat.main.collect_local_files')
    @patch('codeconcat.main.parse_code_files')
    @patch('codeconcat.main.write_markdown')
    @patch('codeconcat.main.validate_config_values')
    def test_run_codeconcat_basic(self, mock_validate, mock_write, mock_parse, mock_collect):
        """Test basic run_codeconcat execution."""
        # Setup mocks
        mock_collect.return_value = [MagicMock()]
        mock_parse.return_value = ([MagicMock()], [])
        mock_write.return_value = "Test output"
        
        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = '/test'
        config.format = 'markdown'
        config.output = 'output.md'
        config.suppress_comments = False
        config.line_numbers = False
        config.no_codeblock = False
        config.enable_compression = False
        config.extract_docs = False
        config.disable_annotations = True
        config.sort_files = False
        config.disable_progress_bar = True
        config.verbose = False
        config.include_repo_overview = False
        config.include_file_index = False
        config.include_directory_structure = False
        config.source_url = None
        config.enable_semgrep = False
        
        # Mock model_dump to return a proper dictionary
        config.model_dump.return_value = {
            'target_path': '/test',
            'format': 'markdown',
            'output': 'output.md',
            'suppress_comments': False,
            'line_numbers': False,
            'no_codeblock': False,
            'enable_compression': False,
            'extract_docs': False,
            'disable_annotations': True,
            'sort_files': False,
            'disable_progress_bar': True,
            'verbose': False,
            'include_repo_overview': False,
            'include_file_index': False,
            'include_directory_structure': False,
            'source_url': None
        }
        
        result = run_codeconcat(config)
        
        assert isinstance(result, str)
        mock_collect.assert_called()
        mock_parse.assert_called()

    @patch('codeconcat.main.collect_local_files')
    @patch('codeconcat.main.validate_config_values')
    def test_run_codeconcat_no_files(self, mock_validate, mock_collect):
        """Test run_codeconcat with no files found."""
        mock_collect.return_value = []
        
        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = '/empty'
        config.format = 'markdown'
        config.source_url = None
        config.enable_semgrep = False
        config.disable_progress_bar = True
        config.verbose = False
        
        # Mock model_dump to return a proper dictionary
        config.model_dump.return_value = {
            'target_path': '/empty',
            'format': 'markdown',
            'source_url': None
        }
        
        with pytest.raises(FileProcessingError, match="No files were successfully parsed"):
            run_codeconcat(config)


class TestRunCodeConcatInMemory:
    """Test suite for run_codeconcat_in_memory function."""

    @patch('codeconcat.main.collect_local_files')
    @patch('codeconcat.main.parse_code_files')
    @patch('codeconcat.main.validate_config_values')
    def test_run_in_memory_returns_string(self, mock_validate, mock_parse, mock_collect):
        """Test that run_codeconcat_in_memory returns a string."""
        mock_collect.return_value = [MagicMock()]
        mock_parse.return_value = ([MagicMock()], [])
        
        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = '/test'
        config.format = 'markdown'
        config.suppress_comments = False
        config.line_numbers = False
        config.no_codeblock = False
        config.enable_compression = False
        config.extract_docs = False
        config.disable_annotations = True
        config.sort_files = False
        config.disable_progress_bar = True
        config.verbose = False
        config.include_repo_overview = False
        config.include_file_index = False
        config.include_directory_structure = False
        config.source_url = None
        config.enable_semgrep = False
        
        # Mock model_dump to return a proper dictionary
        config.model_dump.return_value = {
            'target_path': '/test',
            'format': 'markdown',
            'suppress_comments': False,
            'line_numbers': False,
            'no_codeblock': False,
            'enable_compression': False,
            'extract_docs': False,
            'disable_annotations': True,
            'sort_files': False,
            'disable_progress_bar': True,
            'verbose': False,
            'include_repo_overview': False,
            'include_file_index': False,
            'include_directory_structure': False,
            'source_url': None
        }
        
        with patch('codeconcat.main.write_markdown', return_value="Test output"):
            result = run_codeconcat_in_memory(config)
        
        assert isinstance(result, str)


class TestWriteOutputFiles:
    """Test suite for _write_output_files function."""

    @patch('builtins.open', new_callable=mock_open)
    def test_write_output_files_single_file(self, mock_file):
        """Test writing to a single output file."""
        config = MagicMock(spec=CodeConCatConfig)
        config.output = 'output.md'
        config.format = 'markdown'
        config.target_path = None
        config.disable_progress_bar = True
        
        _write_output_files("Test content", config)
        
        mock_file.assert_called_once_with('output.md', 'w', encoding='utf-8')
        mock_file().write.assert_called_with("Test content")

    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_write_output_files_stdout(self, mock_print, mock_file):
        """Test writing to file when output is '-' (stdout no longer supported)."""
        config = MagicMock(spec=CodeConCatConfig)
        config.output = '-'
        config.format = 'markdown'
        config.target_path = None
        config.disable_progress_bar = True
        
        _write_output_files("Test content", config)
        
        # Since stdout is no longer supported, it will write to a file named '-'
        mock_file.assert_called_once_with('-', 'w', encoding='utf-8')
        mock_file().write.assert_called_with("Test content")


class TestMainFunction:
    """Test suite for main function."""

    @patch('sys.argv', ['codeconcat', '--version'])
    @patch('codeconcat.main.cli_entry_point')
    def test_main_version(self, mock_cli):
        """Test main with --version flag."""
        main()
        mock_cli.assert_called_once()

    @patch('sys.argv', ['codeconcat', '--init'])
    @patch('codeconcat.main.cli_entry_point')
    def test_main_create_config(self, mock_cli):
        """Test main with --init flag."""
        main()
        mock_cli.assert_called_once()

    @patch('sys.argv', ['codeconcat', '/test/path'])
    @patch('codeconcat.main.cli_entry_point')
    def test_main_normal_execution(self, mock_cli):
        """Test main with normal execution."""
        main()
        mock_cli.assert_called_once()

    @patch('sys.argv', ['codeconcat'])
    @patch('codeconcat.main.cli_entry_point')
    def test_main_no_args(self, mock_cli):
        """Test main with no arguments."""
        main()
        mock_cli.assert_called_once()


class TestCliEntryPoint:
    """Test suite for cli_entry_point function."""

    @patch('codeconcat.main.build_parser')
    def test_cli_entry_point(self, mock_build_parser):
        """Test CLI entry point."""
        # Create a mock parser that returns mock args
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.init = False
        mock_args.reconstruct = None
        mock_args.show_config = False
        mock_args.show_config_detail = False
        mock_args.verify_dependencies = False
        mock_args.diagnose_parser = None
        mock_args.verbose = 0
        mock_args.debug = False
        mock_args.quiet = False
        mock_args.preset = 'medium'
        mock_args.config = None
        mock_args.target_path = '.'
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        
        with patch('codeconcat.main.run_codeconcat') as mock_run:
            mock_run.return_value = "test output"
            with patch('codeconcat.main._write_output_files'):
                cli_entry_point()
        
        mock_build_parser.assert_called_once()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_generate_folder_tree_empty_dir(self):
        """Test folder tree generation for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = MagicMock(spec=CodeConCatConfig)
            config.exclude_patterns = []
            config.use_gitignore = False
            config.use_default_excludes = False
            config.exclude_paths = []
            config.include_paths = []
            config.doc_extensions = ['.md', '.rst', '.txt']
            config.include_languages = None
            config.exclude_languages = None
            config.verbose = False
            config.target_path = tmpdir
            config.parser_engine = 'tree_sitter'
            
            tree = generate_folder_tree(tmpdir, config)
            assert isinstance(tree, str)
            # Empty directory should still show the directory name
            assert os.path.basename(tmpdir) in tree

    def test_generate_folder_tree_nonexistent_dir(self):
        """Test folder tree generation for nonexistent directory."""
        config = MagicMock(spec=CodeConCatConfig)
        config.exclude_patterns = []
        config.use_gitignore = False
        config.use_default_excludes = False
        config.exclude_paths = []
        config.include_paths = []
        config.doc_extensions = ['.md', '.rst', '.txt']
        config.include_languages = None
        config.exclude_languages = None
        config.verbose = False
        config.target_path = '/nonexistent/path'
        config.parser_engine = 'tree_sitter'
        
        # Should return empty string for nonexistent path
        tree = generate_folder_tree('/nonexistent/path', config)
        assert isinstance(tree, str)
        assert tree == ""  # No files found for nonexistent path

    @patch('codeconcat.main.collect_local_files')
    @patch('codeconcat.main.parse_code_files')
    @patch('codeconcat.main.write_markdown')
    @patch('codeconcat.main.validate_config_values')
    def test_run_codeconcat_with_errors(self, mock_validate, mock_write_markdown, mock_parse, mock_collect):
        """Test run_codeconcat with parsing errors."""
        from codeconcat.base_types import ParsedFileData
        
        parsed_file = MagicMock(spec=ParsedFileData)
        parsed_file.file_path = '/test/file.py'
        parsed_file.language = 'python'
        parsed_file.content = 'test content'
        
        # Create proper error objects
        error1 = MagicMock()
        error1.file_path = '/test/file1.py'
        error1.__str__.return_value = "Error 1"
        
        error2 = MagicMock()
        error2.file_path = '/test/file2.py'
        error2.__str__.return_value = "Error 2"
        
        mock_collect.return_value = [parsed_file]
        mock_parse.return_value = ([parsed_file], [error1, error2])
        mock_write_markdown.return_value = "# Test Output\n\nFile content here"
        
        config = MagicMock(spec=CodeConCatConfig)
        config.target_path = '/test'
        config.format = 'markdown'
        config.output_path = 'output.md'
        config.suppress_comments = False
        config.line_numbers = False
        config.no_codeblock = False
        config.enable_compression = False
        config.extract_docs = False
        config.disable_annotations = True
        config.sort_files = False
        config.disable_progress_bar = True
        config.verbose = False
        config.source_url = None
        config.enable_semgrep = False
        config.include_repo_overview = False
        config.include_file_index = False
        config.include_directory_structure = False
        
        # Mock model_dump to return a proper dictionary
        config.model_dump.return_value = {
            'target_path': '/test',
            'format': 'markdown',
            'output_path': 'output.md',
            'suppress_comments': False,
            'line_numbers': False,
            'no_codeblock': False,
            'enable_compression': False,
            'extract_docs': False,
            'disable_annotations': True,
            'sort_files': False,
            'disable_progress_bar': True,
            'verbose': False,
            'source_url': None
        }
        
        result = run_codeconcat(config)
        
        assert result is not None
        assert len(result) > 0