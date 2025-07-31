import unittest
from unittest.mock import patch, MagicMock
from marcus.observability import logging as obs_logging

class TestGetLogger(unittest.TestCase):
    @patch('marcus.observability.logging.logging')
    def test_get_logger_with_name(self, mock_logging):
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        mock_logger.hasHandlers.return_value = True

        logger = obs_logging.get_logger('test_logger')
        self.assertEqual(logger, mock_logger)
        mock_logging.getLogger.assert_called_once_with('test_logger')
        mock_logger.hasHandlers.assert_called_once()

    @patch('marcus.observability.logging.logging')
    @patch('marcus.observability.logging.sys')
    def test_get_logger_without_handlers(self, mock_sys, mock_logging):
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        mock_logger.hasHandlers.return_value = False
        mock_handler = MagicMock()
        mock_formatter = MagicMock()
        mock_logging.StreamHandler.return_value = mock_handler
        mock_logging.Formatter.return_value = mock_formatter

        logger = obs_logging.get_logger('test_logger')
        self.assertEqual(logger, mock_logger)
        mock_logging.getLogger.assert_called_once_with('test_logger')
        mock_logger.hasHandlers.assert_called_once()
        mock_logging.StreamHandler.assert_called_once_with(mock_sys.stdout)
        mock_logging.Formatter.assert_called_once_with(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
        )
        mock_handler.setFormatter.assert_called_once_with(mock_formatter)
        mock_logger.addHandler.assert_called_once_with(mock_handler)
        mock_logger.setLevel.assert_called_once_with(mock_logging.INFO)

    def test_get_logger_default_name(self):
        import logging
        # Should not raise error and should return a logger
        logger = obs_logging.get_logger()
        self.assertIsInstance(logger, logging.Logger)
