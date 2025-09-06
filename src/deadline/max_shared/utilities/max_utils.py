# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Shared 3ds Max utilities for Deadline Cloud integration.

This module contains pymxs utilities that are shared between the submitter and adaptor
components to ensure consistent behavior for render elements detection, validation,
and management.
"""

import logging
import os
from pathlib import Path

import pymxs  # separate import to initialize  # noqa: F401
from pymxs import runtime as rt

_logger = logging.getLogger(__name__)


def get_render_elements() -> list:
    """
    Gets all render elements present in the max scene with their properties.

    This function provides comprehensive render element detection that matches
    Deadline 10's functionality, including V-Ray VFB detection and element
    index tracking for later manipulation.

    :returns: a list of dictionaries containing render element information
              Each dictionary contains: index, name, type, enabled, output_filename,
              has_output_path, vray_vfb, element_object
    :return_type: list[dict]
    """
    render_elements = []

    try:
        # Get render element manager
        re_manager = rt.maxOps.GetCurRenderElementMgr()
        if not re_manager:
            _logger.warning("No render element manager found")
            return render_elements

        # Iterate through all render elements
        for i in range(re_manager.NumRenderElements()):
            element = re_manager.GetRenderElement(i)
            if not element:
                continue

            # Skip Missing_Render_Element_Plug_in (Deadline 10 pattern)
            if rt.classof(element) == rt.Missing_Render_Element_Plug_in:
                _logger.debug(f"Skipping missing render element plugin at index {i}")
                continue

            # Extract render element information with enhanced properties
            element_info = {
                "index": i,
                "name": (
                    str(element.elementName) if hasattr(element, "elementName") else f"Element_{i}"
                ),
                "type": str(rt.classof(element)),
                "enabled": bool(re_manager.GetRenderElementEnabled(i)),
                "output_filename": "",
                "has_output_path": False,
                "vray_vfb": False,
                "element_object": element,  # Store reference for later manipulation
            }

            # Get output filename if available
            try:
                output_filename = re_manager.GetRenderElementFilename(i)
                if output_filename:
                    element_info["output_filename"] = str(output_filename).replace("\\", "/")
                    element_info["has_output_path"] = True
            except Exception as e:
                _logger.debug(f"Could not get output filename for render element {i}: {e}")

            # Check for V-Ray VFB property (V-Ray specific)
            try:
                if hasattr(element, "vrayVFB"):
                    element_info["vray_vfb"] = bool(element.vrayVFB)
            except Exception as e:
                _logger.debug(f"Could not get V-Ray VFB property for render element {i}: {e}")

            render_elements.append(element_info)

    except Exception as e:
        _logger.error(f"Error getting render elements: {e}")

    return render_elements


def validate_render_element_paths(render_elements: list) -> list:
    """
    Validates render element output paths and returns warnings for problematic paths.

    This function provides comprehensive path validation matching Deadline 10's
    sanity check system for render elements.

    :param render_elements: list of render element dictionaries from get_render_elements()
    :type render_elements: list[dict]
    :returns: list of warning messages for render elements with path issues
    :return_type: list[str]
    """
    warnings = []

    for element in render_elements:
        element_name = element.get("name", "Unknown")
        output_filename = element.get("output_filename", "")
        has_output_path = element.get("has_output_path", False)
        enabled = element.get("enabled", True)

        # Skip disabled render elements
        if not enabled:
            continue

        # Check for missing output paths
        if not has_output_path or not output_filename:
            warnings.append(f"Render element '{element_name}' has no output path specified")
            continue

        # Check if output directory is accessible
        try:
            output_path = Path(output_filename)
            parent_dir = output_path.parent

            if not parent_dir.exists():
                warnings.append(
                    f"Render element '{element_name}' output directory does not exist: {parent_dir}"
                )
            elif not os.access(parent_dir, os.W_OK):
                warnings.append(
                    f"Render element '{element_name}' output directory is not writable: {parent_dir}"
                )

        except (OSError, ValueError) as e:
            warnings.append(
                f"Render element '{element_name}' has invalid output path: {output_filename} ({e})"
            )

    return warnings


def get_render_elements_output_directories() -> set:
    """
    Gets all unique output directories from render elements in the scene.

    This function is used by both the submitter (for job bundle asset management)
    and the adaptor (for directory creation and validation).

    :returns: set of directory paths where render elements will be output
    :return_type: set[str]
    """
    output_dirs = set()

    try:
        render_elements = get_render_elements()
        for element in render_elements:
            output_filename = element.get("output_filename", "")
            if output_filename and element.get("enabled", True):
                try:
                    output_path = Path(output_filename)
                    parent_dir = str(output_path.parent).replace("\\", "/")
                    if parent_dir and parent_dir != ".":
                        output_dirs.add(parent_dir)
                except (OSError, ValueError):
                    continue

    except Exception as e:
        _logger.error(f"Error getting render element output directories: {e}")

    return output_dirs


def purify_render_element_name(element_name: str) -> str:
    """
    Purifies render element names by removing invalid characters for file paths.

    This matches Deadline 10's render element name purification logic to ensure
    consistent naming between GUI submission and render execution.

    :param element_name: original render element name
    :type element_name: str
    :returns: purified element name safe for file paths
    :return_type: str
    """
    if not element_name:
        return "Element"

    # Replace invalid characters with underscores
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "/", "\\"]
    purified_name = element_name

    for char in invalid_chars:
        purified_name = purified_name.replace(char, "_")

    # Remove leading/trailing spaces and dots
    purified_name = purified_name.strip(" .")

    # Ensure name is not empty after purification
    if not purified_name:
        purified_name = "Element"

    return purified_name


def get_render_element_by_name(element_name: str) -> dict:
    """
    Gets a specific render element by name.

    :param element_name: name of the render element to find
    :type element_name: str
    :returns: render element dictionary or None if not found
    :return_type: dict or None
    """
    render_elements = get_render_elements()

    for element in render_elements:
        if element.get("name") == element_name:
            return element

    return None


def validate_render_element_configuration(render_elements: list, settings: dict) -> list:
    """
    Validates render element configuration against settings.

    This function provides comprehensive validation of render element settings
    to ensure consistency between GUI configuration and render execution.

    :param render_elements: list of render element dictionaries
    :type render_elements: list[dict]
    :param settings: render element settings dictionary
    :type settings: dict
    :returns: list of validation warnings
    :return_type: list[str]
    """
    warnings = []

    if not render_elements:
        return warnings

    # Validate ignore by name settings
    ignore_by_name = settings.get("ignore_render_elements_by_name", [])
    if ignore_by_name:
        element_names = [element.get("name", "") for element in render_elements]
        for ignored_name in ignore_by_name:
            if ignored_name not in element_names:
                warnings.append(
                    f"Render element '{ignored_name}' specified in ignore list but not found in scene"
                )

    # Validate path settings consistency
    if settings.get("render_elements_update_paths", True):
        path_warnings = validate_render_element_paths(render_elements)
        warnings.extend(path_warnings)

    return warnings


def configure_render_element_paths(render_elements: list, settings: dict) -> list:
    """
    Configures render element paths based on settings.
    
    This function updates render element paths and filenames according to
    Deadline 10's path management system, including name/type inclusion options.

    :param render_elements: list of render element dictionaries
    :type render_elements: list[dict]
    :param settings: render element settings dictionary
    :type settings: dict
    :returns: list of configuration warnings
    :return_type: list[str]
    """
    warnings = []
    
    if not render_elements or not settings.get("render_elements_update_paths", True):
        return warnings
    
    try:
        re_manager = rt.maxOps.GetCurRenderElementMgr()
        if not re_manager:
            warnings.append("No render element manager found")
            return warnings
        
        for element in render_elements:
            element_index = element.get("index", -1)
            element_name = element.get("name", "")
            element_type = element.get("type", "")
            
            if element_index < 0:
                continue
            
            # Build new path based on settings
            base_path = element.get("output_filename", "")
            if not base_path:
                continue
            
            # Apply path modifications based on settings
            new_path = _build_render_element_path(
                base_path, element_name, element_type, settings
            )
            
            # Update render element path
            try:
                re_manager.SetRenderElementFilename(element_index, new_path)
                _logger.debug(f"Updated render element '{element_name}' path to: {new_path}")
            except Exception as e:
                warnings.append(f"Failed to update path for render element '{element_name}': {e}")
    
    except Exception as e:
        _logger.error(f"Error configuring render element paths: {e}")
        warnings.append(f"Path configuration failed: {e}")
    
    return warnings


def configure_vray_render_elements(render_elements: list, settings: dict) -> list:
    """
    Configures V-Ray specific render element settings.
    
    This function handles V-Ray VFB control and split buffer support
    matching Deadline 10's V-Ray integration.

    :param render_elements: list of render element dictionaries
    :type render_elements: list[dict]
    :param settings: render element settings dictionary
    :type settings: dict
    :returns: list of configuration warnings
    :return_type: list[str]
    """
    warnings = []
    
    if not render_elements:
        return warnings
    
    vfb_control = settings.get("vray_render_elements_vfb_control", True)
    split_buffer = settings.get("vray_split_buffer_support", True)
    
    try:
        for element in render_elements:
            element_obj = element.get("element_object")
            if not element_obj:
                continue
            
            element_name = element.get("name", "")
            
            # Configure V-Ray VFB control
            if hasattr(element_obj, "vrayVFB"):
                try:
                    # Disable VFB for render elements when VFB control is enabled
                    element_obj.vrayVFB = not vfb_control
                    _logger.debug(f"Set V-Ray VFB for '{element_name}': {not vfb_control}")
                except Exception as e:
                    warnings.append(f"Failed to configure V-Ray VFB for '{element_name}': {e}")
            
            # Additional V-Ray specific configurations can be added here
            # based on element type and settings
    
    except Exception as e:
        _logger.error(f"Error configuring V-Ray render elements: {e}")
        warnings.append(f"V-Ray configuration failed: {e}")
    
    return warnings


def store_original_render_element_state(render_elements: list) -> dict:
    """
    Stores original render element state for later restoration.
    
    This function captures the current state of render elements
    to enable restoration after rendering completes.

    :param render_elements: list of render element dictionaries
    :type render_elements: list[dict]
    :returns: dictionary containing original state information
    :return_type: dict
    """
    original_state = {
        "element_names": [],
        "element_paths": [],
        "element_enabled": [],
        "vray_vfb_states": [],
    }
    
    try:
        re_manager = rt.maxOps.GetCurRenderElementMgr()
        if not re_manager:
            return original_state
        
        for element in render_elements:
            element_index = element.get("index", -1)
            element_obj = element.get("element_object")
            
            if element_index < 0:
                continue
            
            # Store original names and paths
            original_state["element_names"].append(element.get("name", ""))
            original_state["element_paths"].append(element.get("output_filename", ""))
            original_state["element_enabled"].append(element.get("enabled", True))
            
            # Store V-Ray VFB states
            if element_obj and hasattr(element_obj, "vrayVFB"):
                try:
                    original_state["vray_vfb_states"].append(bool(element_obj.vrayVFB))
                except Exception:
                    original_state["vray_vfb_states"].append(False)
            else:
                original_state["vray_vfb_states"].append(False)
    
    except Exception as e:
        _logger.error(f"Error storing original render element state: {e}")
    
    return original_state


def restore_original_render_element_state(original_state: dict) -> list:
    """
    Restores original render element state.
    
    This function restores render elements to their original state
    using previously stored state information.

    :param original_state: dictionary containing original state information
    :type original_state: dict
    :returns: list of restoration warnings
    :return_type: list[str]
    """
    warnings = []
    
    if not original_state:
        return warnings
    
    try:
        re_manager = rt.maxOps.GetCurRenderElementMgr()
        if not re_manager:
            warnings.append("No render element manager found for restoration")
            return warnings
        
        render_elements = get_render_elements()
        
        for i, element in enumerate(render_elements):
            element_index = element.get("index", -1)
            element_obj = element.get("element_object")
            
            if element_index < 0 or i >= len(original_state.get("element_paths", [])):
                continue
            
            # Restore original paths
            try:
                original_path = original_state["element_paths"][i]
                if original_path:
                    re_manager.SetRenderElementFilename(element_index, original_path)
            except Exception as e:
                warnings.append(f"Failed to restore path for render element {i}: {e}")
            
            # Restore V-Ray VFB states
            if (element_obj and hasattr(element_obj, "vrayVFB") and 
                i < len(original_state.get("vray_vfb_states", []))):
                try:
                    element_obj.vrayVFB = original_state["vray_vfb_states"][i]
                except Exception as e:
                    warnings.append(f"Failed to restore V-Ray VFB state for render element {i}: {e}")
    
    except Exception as e:
        _logger.error(f"Error restoring original render element state: {e}")
        warnings.append(f"State restoration failed: {e}")
    
    return warnings


def _build_render_element_path(base_path: str, element_name: str, element_type: str, settings: dict) -> str:
    """
    Builds render element path based on naming settings.
    
    This is a private helper function that constructs the final path
    based on Deadline 10's path building logic.

    :param base_path: original base path
    :type base_path: str
    :param element_name: render element name
    :type element_name: str
    :param element_type: render element type
    :type element_type: str
    :param settings: path building settings
    :type settings: dict
    :returns: constructed path
    :return_type: str
    """
    try:
        path_obj = Path(base_path)
        directory = path_obj.parent
        filename = path_obj.stem
        extension = path_obj.suffix
        
        # Build directory path modifications
        if settings.get("render_elements_include_name_in_path", True):
            purified_name = purify_render_element_name(element_name)
            directory = directory / purified_name
        
        if settings.get("render_elements_include_type_in_path", False):
            purified_type = purify_render_element_name(element_type)
            directory = directory / purified_type
        
        # Build filename modifications
        if settings.get("render_elements_include_name_in_filename", True):
            purified_name = purify_render_element_name(element_name)
            filename = f"{filename}_{purified_name}"
        
        if settings.get("render_elements_include_type_in_filename", False):
            purified_type = purify_render_element_name(element_type)
            filename = f"{filename}_{purified_type}"
        
        # Construct final path
        final_path = directory / f"{filename}{extension}"
        return str(final_path).replace("\\", "/")
    
    except Exception as e:
        _logger.error(f"Error building render element path: {e}")
        return base_path