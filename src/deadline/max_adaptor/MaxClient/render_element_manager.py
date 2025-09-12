"""
3ds Max Deadline Cloud Adaptor - Render Element Manager

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
"""

import logging
from typing import Any, Dict, List, Optional

import pymxs  # noqa
from pymxs import runtime as rt

# Import shared utilities for consistent behavior with submitter
from deadline.max_shared.utilities.max_utils import (
    configure_render_element_paths,
    configure_vray_render_elements,
    get_render_elements,
    restore_original_render_element_state,
    store_original_render_element_state,
    validate_render_element_configuration,
)

logger = logging.getLogger(__name__)


class RenderElementManager:
    """
    Comprehensive render element management using pymxs (based on Deadline 10's system).

    This class handles all render element configuration during rendering, including:
    - Basic render element enable/disable
    - Ignore settings (all elements or by name)
    - Path and filename updates with naming patterns
    - V-Ray VFB integration and split buffer support
    - Original state storage and restoration
    """

    def __init__(self, client):
        """
        Initialize the render element manager.

        Args:
            client: The MaxClient instance for communication
        """
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.re_manager = None
        self.original_state = {}

    def configure_render_elements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive render element configuration matching Deadline 10.

        Args:
            data: Dictionary containing render element configuration parameters

        Returns:
            Dictionary with success status and any messages/errors
        """
        try:
            self.logger.info("Starting render elements configuration")
            self.logger.info(f"Received configuration data: {data}")

            # Get render element manager
            self.re_manager = rt.maxOps.GetCurRenderElementMgr()
            if not self.re_manager:
                raise Exception("Failed to get render element manager")

            # Get current render elements from scene
            render_elements = get_render_elements()
            if not render_elements:
                self.logger.info("No render elements found in scene")
                return {"success": True, "message": "No render elements to configure"}

            self.logger.info(f"Found {len(render_elements)} render elements in scene:")
            for i, element in enumerate(render_elements):
                self.logger.info(
                    f"  [{i}] {element.get('name', 'Unknown')} - Type: {element.get('type', 'Unknown')} - Enabled: {element.get('enabled', False)} - Output: {element.get('output_filename', 'None')}"
                )

            # Store original state for restoration
            self.original_state = store_original_render_element_state(render_elements)
            self.logger.debug(f"Stored original state for {len(render_elements)} render elements")

            # Configure basic settings
            elements_enabled = data.get("RenderElements", "true").lower() == "true"
            self.logger.info(f"Setting render elements active: {elements_enabled}")
            self.re_manager.SetElementsActive(elements_enabled)

            # Log all render element parameters received
            self.logger.info("Render element configuration parameters:")
            for key, value in data.items():
                if key.lower().startswith(("render_element", "vray_", "ignore_render")):
                    self.logger.info(f"  {key}: {value}")

            if not elements_enabled:
                self.logger.info("Render elements disabled, skipping further configuration")
                return {"success": True, "message": "Render elements disabled"}

            # Handle ignore settings
            self._handle_ignore_settings(data, render_elements)

            # Update paths and filenames if requested
            if data.get("RenderElementsUpdatePaths", "true").lower() == "true":
                self._update_paths_and_filenames(data, render_elements)

            # Handle V-Ray specific settings
            self._configure_vray_settings(data, render_elements)

            # Validate final configuration
            settings = self._convert_data_to_settings(data)
            validation_warnings = validate_render_element_configuration(render_elements, settings)
            if validation_warnings:
                for warning in validation_warnings:
                    self.logger.warning(f"Configuration validation: {warning}")

            self.logger.info("Render elements configuration completed successfully")
            return {"success": True, "message": "Render elements configured successfully"}

        except Exception as e:
            self.logger.error(f"Failed to configure render elements: {e}")
            return {"success": False, "error": str(e)}

    def _handle_ignore_settings(
        self, data: Dict[str, Any], render_elements: List[Dict[str, Any]]
    ) -> None:
        """
        Handle render element ignore settings.

        Args:
            data: Configuration parameters
            render_elements: List of render elements from scene
        """
        # Handle ignore by name list
        ignore_names_str = data.get("IgnoreRenderElementsByName", "")
        if ignore_names_str:
            ignore_names = [name.strip() for name in ignore_names_str.split(",") if name.strip()]
            self.logger.info(f"Ignoring render elements by name: {ignore_names}")

            disabled_count = 0
            for element in render_elements:
                element_name = element.get("name", "")
                if element_name in ignore_names:
                    element_index = element.get("index", -1)
                    if element_index >= 0:
                        self.re_manager.SetRenderElementEnabled(element_index, False)
                        self.logger.info(
                            f"DISABLED render element: '{element_name}' (index {element_index})"
                        )
                        disabled_count += 1

            self.logger.info(f"Disabled {disabled_count} render elements based on ignore list")

    def _update_paths_and_filenames(
        self, data: Dict[str, Any], render_elements: List[Dict[str, Any]]
    ) -> None:
        """
        Update render element paths and filenames based on configuration.

        Args:
            data: Configuration parameters
            render_elements: List of render elements from scene
        """
        try:
            self.logger.info("Updating render element paths and filenames")

            # Configure paths using shared utilities
            path_warnings = configure_render_element_paths(render_elements, data)
            if path_warnings:
                for warning in path_warnings:
                    self.logger.warning(f"Path configuration: {warning}")

        except Exception as e:
            self.logger.error(f"Failed to update render element paths: {e}")
            raise

    def _configure_vray_settings(
        self, data: Dict[str, Any], render_elements: List[Dict[str, Any]]
    ) -> None:
        """
        Configure V-Ray specific render element settings.

        Args:
            data: Configuration parameters
            render_elements: List of render elements from scene
        """
        try:
            # Check if V-Ray VFB control is enabled
            vfb_control = data.get("VRayRenderElementsVFBControl", "true").lower() == "true"
            split_buffer = data.get("VRaySplitBufferSupport", "true").lower() == "true"

            if vfb_control or split_buffer:
                self.logger.info(
                    f"Configuring V-Ray settings - VFB Control: {vfb_control}, Split Buffer: {split_buffer}"
                )

                vray_settings = {
                    "vray_render_elements_vfb_control": vfb_control,
                    "vray_split_buffer_support": split_buffer,
                }

                vray_warnings = configure_vray_render_elements(render_elements, vray_settings)
                if vray_warnings:
                    for warning in vray_warnings:
                        self.logger.warning(f"V-Ray configuration: {warning}")

        except Exception as e:
            self.logger.error(f"Failed to configure V-Ray settings: {e}")
            raise

    def validate_render_elements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate render element configuration without making changes.

        Args:
            data: Dictionary containing render element configuration parameters

        Returns:
            Dictionary with validation results
        """
        try:
            self.logger.info("Validating render elements configuration")

            # Get current render elements from scene
            render_elements = get_render_elements()

            # Validate configuration using shared utilities
            settings = self._convert_data_to_settings(data)
            validation_warnings = validate_render_element_configuration(render_elements, settings)

            return {
                "success": True,
                "element_count": len(render_elements),
                "warnings": validation_warnings,
            }

        except Exception as e:
            self.logger.error(f"Failed to validate render elements: {e}")
            return {"success": False, "error": str(e)}

    def restore_render_elements(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Restore render elements to their original state.

        Args:
            data: Optional configuration data (unused but kept for interface consistency)

        Returns:
            Dictionary with restoration results
        """
        try:
            if not self.original_state:
                self.logger.info("No original state to restore")
                return {"success": True, "message": "No original state to restore"}

            self.logger.info("Restoring render elements to original state")

            # Restore using shared utilities
            restore_warnings = restore_original_render_element_state(self.original_state)
            if restore_warnings:
                for warning in restore_warnings:
                    self.logger.warning(f"Restoration: {warning}")

            # Clear stored state
            self.original_state = {}

            self.logger.info("Render elements restored successfully")
            return {"success": True, "message": "Render elements restored successfully"}

        except Exception as e:
            self.logger.error(f"Failed to restore render elements: {e}")
            return {"success": False, "error": str(e)}

    def _convert_data_to_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert OpenJD data format to settings format expected by shared utilities.

        Args:
            data: OpenJD data dictionary

        Returns:
            Settings dictionary compatible with shared utilities
        """
        settings = {}

        # Convert ignore render elements by name
        ignore_names_str = data.get("IgnoreRenderElementsByName", "")
        if ignore_names_str:
            settings["ignore_render_elements_by_name"] = [
                name.strip() for name in ignore_names_str.split(",") if name.strip()
            ]
        else:
            settings["ignore_render_elements_by_name"] = []

        # Convert boolean settings
        settings["render_elements_update_paths"] = (
            data.get("RenderElementsUpdatePaths", "true").lower() == "true"
        )

        return settings
