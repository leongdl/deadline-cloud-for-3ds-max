# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
from __future__ import annotations
from unittest.mock import patch, Mock

import pytest
from deadline.max_adaptor.MaxClient.render_handlers import DefaultMaxHandler
from deadline.max_adaptor.executable_handler import MaxExecutableHandler


@pytest.fixture
def maxhandlerbase():
    return DefaultMaxHandler()


class TestDefaultMaxHandler:
    @pytest.mark.parametrize("args", [{"output_file_path": "C:/Users/Sandie/Desktop"}])
    def test_set_output_file_path(self, maxhandlerbase: DefaultMaxHandler, args: dict):
        """Tests that setting the image height calls the correct functions"""
        # WHEN
        maxhandlerbase.set_output_file_path(args)

        # THEN
        assert maxhandlerbase.output_dir == args["output_file_path"]

    @pytest.mark.parametrize("args", [{"output_file_name": "Output__#####"}])
    def test_set_output_file_name(self, maxhandlerbase: DefaultMaxHandler, args: dict):
        """Tests that setting the image height calls the correct functions"""
        # WHEN
        maxhandlerbase.set_output_file_name(args)

        # THEN
        assert maxhandlerbase.output_name == args["output_file_name"]

    @pytest.mark.parametrize("args", [{"output_file_format": ".png"}])
    def test_set_output_file_format(self, maxhandlerbase: DefaultMaxHandler, args: dict):
        """Tests that setting the image height calls the correct functions"""
        # WHEN
        maxhandlerbase.set_output_file_format(args)

        # THEN
        assert maxhandlerbase.output_format == args["output_file_format"]

    @patch("deadline.max_adaptor.MaxClient.render_handlers.default_max_handler.rt")
    @patch.object(MaxExecutableHandler, "is_executable_type")
    def test_log_to_console(
        self,
        mock_executable_handler: Mock,
        mock_rt: Mock,
        maxhandlerbase: DefaultMaxHandler,
        capsys: pytest.CaptureFixture,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_executable_handler.return_value = False
        test_message_3dsmax: str = "3dsmax test message"

        maxhandlerbase.log_to_console(test_message_3dsmax)

        captured_result = capsys.readouterr()
        assert captured_result.out == f"{test_message_3dsmax}\n"
        assert not mock_rt.logsystem.logEntry.called

        mock_executable_handler.return_value = True
        test_message_3dsmaxbatch: str = "3dsmaxbatch test message"

        maxhandlerbase.log_to_console(test_message_3dsmaxbatch)

        captured_result = capsys.readouterr()
        assert test_message_3dsmaxbatch not in captured_result.out
        mock_rt.logsystem.logEntry.assert_called_once_with(test_message_3dsmaxbatch, broadcast=True)

    def test_set_client(self, maxhandlerbase: DefaultMaxHandler):
        """Tests that setting the client reference works correctly"""
        # GIVEN
        mock_client = Mock()

        # WHEN
        maxhandlerbase.set_client(mock_client)

        # THEN
        assert maxhandlerbase.client == mock_client

    def test_configure_render_elements_no_client(self, maxhandlerbase: DefaultMaxHandler):
        """Tests that configure_render_elements handles missing client gracefully"""
        # GIVEN
        data = {"RenderElements": "true"}

        # WHEN/THEN - Should not raise exception
        maxhandlerbase.configure_render_elements(data)

    def test_configure_render_elements_with_client(self, maxhandlerbase: DefaultMaxHandler):
        """Tests that configure_render_elements calls client method correctly"""
        # GIVEN
        mock_client = Mock()
        mock_client.configure_render_elements.return_value = {"success": True}
        maxhandlerbase.set_client(mock_client)
        data = {"RenderElements": "true"}

        # WHEN
        maxhandlerbase.configure_render_elements(data)

        # THEN
        mock_client.configure_render_elements.assert_called_once_with(data)

    def test_configure_render_elements_failure(self, maxhandlerbase: DefaultMaxHandler):
        """Tests that configure_render_elements handles client failure correctly"""
        # GIVEN
        mock_client = Mock()
        mock_client.configure_render_elements.return_value = {
            "success": False,
            "error": "Test error",
        }
        maxhandlerbase.set_client(mock_client)
        data = {"RenderElements": "true"}

        # WHEN/THEN
        with pytest.raises(RuntimeError, match="Render elements configuration failed: Test error"):
            maxhandlerbase.configure_render_elements(data)

    def test_cleanup_render_elements_no_client(self, maxhandlerbase: DefaultMaxHandler):
        """Tests that cleanup_render_elements handles missing client gracefully"""
        # GIVEN
        data = {"RenderElements": "true"}

        # WHEN/THEN - Should not raise exception
        maxhandlerbase.cleanup_render_elements(data)

    def test_cleanup_render_elements_with_client(self, maxhandlerbase: DefaultMaxHandler):
        """Tests that cleanup_render_elements calls client method correctly"""
        # GIVEN
        mock_client = Mock()
        mock_client.restore_render_elements.return_value = {"success": True}
        maxhandlerbase.set_client(mock_client)
        data = {"RenderElements": "true"}

        # WHEN
        maxhandlerbase.cleanup_render_elements(data)

        # THEN
        mock_client.restore_render_elements.assert_called_once_with(data)
