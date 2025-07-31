import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from marcus.utils import jwt as jwt_utils

class TestJWTUtils(unittest.TestCase):
    @patch('marcus.utils.jwt.jwt')
    def test_get_user_id_from_jwt_success(self, mock_jose_jwt):
        mock_request = MagicMock()
        token = 'validtoken'
        mock_request.headers.get.return_value = f'Bearer {token}'
        mock_jose_jwt.decode.return_value = {'user_id': 'user123'}
        user_id = jwt_utils.get_user_id_from_jwt(mock_request)
        self.assertEqual(user_id, 'user123')
        mock_jose_jwt.decode.assert_called_once_with(token, jwt_utils.JWT_SECRET, algorithms=[jwt_utils.JWT_ALGORITHM])

    def test_get_user_id_from_jwt_missing_header(self):
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        with self.assertRaises(HTTPException) as ctx:
            jwt_utils.get_user_id_from_jwt(mock_request)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn('Missing or invalid Authorization header', ctx.exception.detail)

    def test_get_user_id_from_jwt_invalid_prefix(self):
        mock_request = MagicMock()
        mock_request.headers.get.return_value = 'Token sometoken'
        with self.assertRaises(HTTPException) as ctx:
            jwt_utils.get_user_id_from_jwt(mock_request)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn('Missing or invalid Authorization header', ctx.exception.detail)

    @patch('marcus.utils.jwt.jwt')
    def test_get_user_id_from_jwt_no_user_id(self, mock_jose_jwt):
        mock_request = MagicMock()
        token = 'validtoken'
        mock_request.headers.get.return_value = f'Bearer {token}'
        mock_jose_jwt.decode.return_value = {}
        with self.assertRaises(HTTPException) as ctx:
            jwt_utils.get_user_id_from_jwt(mock_request)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn('user_id not found in token', ctx.exception.detail)

    @patch('marcus.utils.jwt.get_user_id_from_jwt')
    @patch('marcus.utils.jwt.logger')
    def test_get_jwt_user_id_dep_success(self, mock_logger, mock_get_user_id):
        mock_request = MagicMock()
        mock_get_user_id.return_value = 'user123'
        result = jwt_utils.get_jwt_user_id_dep(mock_request)
        self.assertEqual(result, 'user123')
        mock_logger.error.assert_not_called()

    @patch('marcus.utils.jwt.get_user_id_from_jwt')
    @patch('marcus.utils.jwt.logger')
    def test_get_jwt_user_id_dep_http_exception(self, mock_logger, mock_get_user_id):
        mock_request = MagicMock()
        exc = HTTPException(status_code=401, detail='fail')
        mock_get_user_id.side_effect = exc
        with self.assertRaises(HTTPException):
            jwt_utils.get_jwt_user_id_dep(mock_request)
        mock_logger.error.assert_called_once_with('JWT extraction failed: %s', 'fail')

if __name__ == "__main__":
    unittest.main()
