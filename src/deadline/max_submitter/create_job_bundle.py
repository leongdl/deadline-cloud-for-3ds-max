# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
3ds Max Deadline Cloud Submitter - Functions for generating the job template and parameter values files
"""

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from data_classes import RenderSubmitterUISettings, StateSetData
from data_const import ALL_CAMERAS_STR, ALL_STATE_SETS_STR, ALL_STEREO_CAMERAS_STR
from deadline.client.exceptions import DeadlineOperationError
from utilities import max_utils


def get_job_template(
    default_job_template: dict[str, Any],
    settings: RenderSubmitterUISettings,
    state_sets: list[StateSetData],
    cameras_in_scene: list,
) -> dict[str, Any]:
    """
    Creates a job template based on the current UI settings.

    :param default_job_template: the default 3dsMax job template
    :param settings: a RenderSubmitterUISettings object containing the latest UI settings
    :param state_sets: a list of StateSetData for the submitted state sets
    :param cameras_in_scene: all cameras based on the UI selection
    """
    job_template = _create_param_definitions(
        default_job_template, settings, state_sets, cameras_in_scene
    )
    job_template = _create_step_definitions(job_template, settings, state_sets, cameras_in_scene)

    # If this developer option is enabled, merge the adaptor_override_environment
    if settings.include_adaptor_wheels:
        override_environment = _merge_adaptor_override_environment()

        # There are no parameter conflicts between these two templates, so this works
        job_template["parameterDefinitions"].extend(override_environment["parameterDefinitions"])

        # Add the environment to the end of the template's job environments
        if "jobEnvironments" not in job_template:
            job_template["jobEnvironments"] = []
        job_template["jobEnvironments"].append(override_environment["environment"])

    return job_template


def _create_param_definitions(
    default_job_template: dict[str, Any],
    settings: RenderSubmitterUISettings,
    state_sets: list[StateSetData],
    cameras_in_scene: list,
) -> dict[str, Any]:
    """
    Creates parameter definitions based on the current UI settings.

    :param default_job_template: the default 3dsMax job template
    :param settings: a RenderSubmitterUISettings object containing the latest UI settings
    :param state_sets: a list of StateSetData for the submitted state sets
    :param cameras_in_scene: all cameras based on the UI selection
    """
    job_template = deepcopy(default_job_template)
    # Set the job's name
    job_template["name"] = settings.name
    if settings.description:
        job_template["description"] = settings.description

    # Values that can have different values per state set.
    # First element is the key in the StateSetData object. Second element is the name of the parameter in the template
    possible_multiples = [
        ["frame_range", "Frames"],
        ["output_file_dir", "OutputFilePath"],
        ["output_file_format", "OutputFileFormat"],
        ["image_resolution", "ImageWidth"],
        ["image_resolution", "ImageHeight"],
    ]

    # Check for each of the values that can differ if they do.
    # When they do, create new parameter definitions per state set for that value
    if settings.state_set == ALL_STATE_SETS_STR:
        for possible_multiple in possible_multiples:
            if _check_multiples(state_sets, possible_multiple[0]):
                job_template = _create_state_set_param_definitions(
                    job_template, possible_multiple[1], state_sets
                )

    # Only add camera parameter to template when a specific camera is selected
    if (
        settings.camera_selection != ALL_CAMERAS_STR
        and settings.camera_selection != ALL_STEREO_CAMERAS_STR
    ):
        job_template["parameterDefinitions"].append(
            {
                "name": "Camera",
                "type": "STRING",
                "userInterface": {
                    "control": "DROPDOWN_LIST",
                    "groupLabel": "3dsMax Settings",
                },
                "description": "The image height of the output.",
                "allowedValues": cameras_in_scene,
            }
        )

    # Add render elements parameters if render elements are present in the scene
    render_elements = max_utils.get_render_elements()
    if render_elements:
        # RenderElements parameter - whether to output render elements
        job_template["parameterDefinitions"].append(
            {
                "name": "RenderElements",
                "type": "STRING",
                "userInterface": {
                    "control": "CHECK_BOX",
                    "label": "Output Render Elements",
                    "groupLabel": "Render Elements",
                },
                "description": "Enable or disable render elements output.",
                "default": "true",
                "allowedValues": ["true", "false"],
            }
        )

        # IgnoreRenderElements parameter - whether to ignore all render elements
        job_template["parameterDefinitions"].append(
            {
                "name": "IgnoreRenderElements",
                "type": "STRING",
                "userInterface": {
                    "control": "CHECK_BOX",
                    "label": "Ignore All Render Elements",
                    "groupLabel": "Render Elements",
                },
                "description": "Ignore all render elements in the scene.",
                "default": "false",
                "allowedValues": ["true", "false"],
            }
        )

        # IgnoreRenderElementsByName parameter - list of render element names to ignore
        if any(elem.get("name") for elem in render_elements):
            element_names = [elem.get("name", "") for elem in render_elements if elem.get("name")]
            job_template["parameterDefinitions"].append(
                {
                    "name": "IgnoreRenderElementsByName",
                    "type": "STRING",
                    "userInterface": {
                        "control": "MULTISELECT_DROPDOWN_LIST",
                        "label": "Ignore Render Elements by Name",
                        "groupLabel": "Render Elements",
                    },
                    "description": "List of render element names to ignore during rendering.",
                    "default": "",
                    "allowedValues": element_names,
                }
            )

        # RenderElementOutputFilenames parameter - output filenames for each render element
        if any(elem.get("output_filename") for elem in render_elements):
            job_template["parameterDefinitions"].append(
                {
                    "name": "RenderElementOutputFilenames",
                    "type": "STRING",
                    "userInterface": {
                        "control": "HIDDEN",
                        "groupLabel": "Render Elements",
                    },
                    "description": "Output filenames for each render element (managed automatically).",
                    "default": "",
                }
            )

    return job_template


def _create_state_set_param_definitions(
    job_template: dict[str, Any], type_: str, state_sets: list[StateSetData]
) -> dict[str, Any]:
    """
    Isolates the parameter provided and create state set specific parameter definitions for the provided parameter.

    :param job_template: the job template
    :param type_: the type of the parameter e.g. Frames, ImageWidth, ...
    :param state_sets: list of StateSetData all submitted state sets
    """
    single_param = [
        param for param in job_template["parameterDefinitions"] if param["name"] == type_
    ][0]
    job_template["parameterDefinitions"] = [
        param for param in job_template["parameterDefinitions"] if param["name"] != type_
    ]
    for state_set in state_sets:
        state_set_param = deepcopy(single_param)
        state_set_param["name"] = state_set.state_set + type_
        state_set_param["userInterface"]["groupLabel"] = state_set.ui_group_label
        job_template["parameterDefinitions"].append(state_set_param)

    return job_template


def _create_step_definitions(
    job_template: dict[str, Any],
    settings: RenderSubmitterUISettings,
    state_sets: list[StateSetData],
    cameras_in_scene: list,
) -> dict[str, Any]:
    """
    Creates steps for state sets

    :param job_template: the job template with updated parameter definitions for the job bundle
    :param settings: a RenderSubmitterUISettings object containing the latest UI settings
    :param state_sets: a list of StateSetData for the submitted state sets
    :param cameras_in_scene: all cameras based on the UI selection
    """
    # Replicate default step per state set
    default_step = job_template["steps"][0]
    job_template["steps"] = []

    # Values that can have different values per state set. First element is the key in the StateSetData object.
    # Second element is the parameter in the template. Third element is the value in the init-data.
    possible_multiples = [
        ["output_file_dir", "OutputFilePath", "output_file_path"],
        ["output_file_format", "OutputFileFormat", "output_file_format"],
        ["image_resolution", "ImageWidth", "image_width"],
        ["image_resolution", "ImageHeight", "image_height"],
    ]

    for state_set in state_sets:
        step = deepcopy(default_step)
        job_template["steps"].append(step)

        step["name"] = state_set.state_set
        parameters_space = step["parameterSpace"]

        # Update the 'Param.Frames' reference in the Frame task parameter if there are multiple ranges
        if _check_multiples(state_sets, "frame_range"):
            parameters_space["taskParameterDefinitions"][0]["range"] = (
                "{{Param." + state_set.state_set + "Frames}}"
            )

        # If were submitting all cameras, add 'Camera' to task parameters
        if (
            settings.camera_selection == ALL_CAMERAS_STR
            or settings.camera_selection == ALL_STEREO_CAMERAS_STR
        ):
            parameters_space["taskParameterDefinitions"].append(
                {"name": "Camera", "type": "STRING", "range": cameras_in_scene}
            )
            run_data = step["script"]["embeddedFiles"][0]
            run_data["data"] += "camera: '{{Task.Param.Camera}}'"

        # init data of the step
        init_data = step["stepEnvironments"][0]["script"]["embeddedFiles"][0]
        init_data["data"] = (
            init_data["data"]
            + f"renderer: {state_set.renderer}\n"
            + f"state_set: {state_set.state_set}\n"
            + f"output_file_name: {state_set.output_file_name}\n"
        )

        for possible_multiple in possible_multiples:
            if _check_multiples(state_sets, possible_multiple[0]):
                init_data["data"] += (
                    possible_multiple[2]
                    + ": '{{Param."
                    + state_set.state_set
                    + possible_multiple[1]
                    + "}}'\n"
                )
            else:
                init_data["data"] += (
                    possible_multiple[2] + ": '{{Param." + possible_multiple[1] + "}}'\n"
                )

        # If a specific camera is selected, link to the Camera parameter
        if (
            settings.camera_selection != ALL_CAMERAS_STR
            and settings.camera_selection != ALL_STEREO_CAMERAS_STR
        ):
            init_data["data"] += "camera: '{{Param.Camera}}'\n"

    return job_template


def _merge_adaptor_override_environment():
    """
    Create template for the adaptor override environment
    """
    # TODO see if changes to adaptor_override_environment.yaml need to be made to work on windows worker
    with open(Path(__file__).parent / "adaptor_override_environment.yaml") as f:
        override_environment = yaml.safe_load(f)

    # Read DEVELOPMENT.md for instructions to create the wheels directory.
    wheels_path = Path(__file__).parent.parent.parent.parent / "wheels"
    if not wheels_path.exists() and wheels_path.is_dir():
        raise RuntimeError(
            "The Developer Option 'Include Adaptor Wheels' is enabled, "
            "but the wheels directory does not exist:\n" + str(wheels_path)
        )
    wheels_path_package_names = {
        path.split("-", 1)[0] for path in os.listdir(wheels_path) if path.endswith(".whl")
    }
    if wheels_path_package_names != {
        "openjd_adaptor_runtime",
        "deadline",
        "deadline_cloud_for_3ds_max",
    }:
        raise RuntimeError(
            "The Developer Option 'Include Adaptor Wheels' is enabled, but the wheels directory contains the "
            "wrong wheels:\n"
            + "Expected: openjd_adaptor_runtime, deadline, and deadline_cloud_for_3ds_max\n"
            + f"Actual: {wheels_path_package_names}"
        )

    override_adaptor_wheels_param = [
        param
        for param in override_environment["parameterDefinitions"]
        if param["name"] == "OverrideAdaptorWheels"
    ][0]
    override_adaptor_wheels_param["default"] = str(wheels_path)
    override_adaptor_name_param = [
        param
        for param in override_environment["parameterDefinitions"]
        if param["name"] == "OverrideAdaptorName"
    ][0]
    override_adaptor_name_param["default"] = "3dsmax-openjd"


def get_parameters_values(
    settings: RenderSubmitterUISettings,
    state_sets: list[StateSetData],
    queue_parameters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Creates parameter values based on the current UI settings.

    :param settings: a RenderSubmitterUISettings object containing the latest UI settings
    :param state_sets: a list of StateSetData for the submitted state sets
    :param queue_parameters: the settings from the shared job settings tab
    """
    # Validate render elements parameter consistency
    _validate_render_elements_parameters(settings)

    parameter_values = _get_job_parameters(settings, state_sets)
    queue_parameters = _get_queue_parameters_for_bundle(
        settings, parameter_values, queue_parameters
    )
    parameter_values.extend(
        {"name": param["name"], "value": param["value"]} for param in queue_parameters
    )

    return parameter_values


def _get_job_parameters(
    settings: RenderSubmitterUISettings,
    state_sets: list[StateSetData],
) -> list[dict[str, Any]]:
    """
    Creates all the job parameters on the current UI settings.

    :param settings: a RenderSubmitterUISettings object containing the latest UI settings
    :param state_sets: a list of StateSetData for the submitted state sets
    """
    parameter_values: list[dict[str, Any]] = []

    parameter_values.append({"name": "MaxSceneFile", "value": max_utils.get_scene_path()})

    possible_multiples = [
        ["frame_range", "Frames"],
        ["output_file_dir", "OutputFilePath"],
        ["output_file_format", "OutputFileFormat"],
    ]
    for possible_multiple in possible_multiples:
        if _check_multiples(state_sets, possible_multiple[0]):
            for state_set in state_sets:
                parameter_values.append(
                    {
                        "name": state_set.state_set + possible_multiple[1],
                        "value": getattr(state_set, possible_multiple[0]),
                    }
                )
        else:
            parameter_values.append(
                {
                    "name": possible_multiple[1],
                    "value": getattr(state_sets[0], possible_multiple[0]),
                }
            )

    # Check if there are multiple output resolution
    if _check_multiples(state_sets, "image_resolution"):
        for state_set in state_sets:
            parameter_values.append(
                {
                    "name": state_set.state_set + "ImageWidth",
                    "value": state_set.image_resolution[0],
                }
            )
            parameter_values.append(
                {
                    "name": state_set.state_set + "ImageHeight",
                    "value": state_set.image_resolution[1],
                }
            )
    else:
        parameter_values.append(
            {
                "name": "ImageWidth",
                "value": state_sets[0].image_resolution[0],
            }
        )
        parameter_values.append(
            {
                "name": "ImageHeight",
                "value": state_sets[0].image_resolution[1],
            }
        )

    # Only add camera parameter when a specific camera is selected
    if (
        settings.camera_selection != ALL_CAMERAS_STR
        and settings.camera_selection != ALL_STEREO_CAMERAS_STR
    ):
        parameter_values.append({"name": "Camera", "value": settings.camera_selection})

    # Add render elements parameters if render elements are present in the scene
    render_elements = max_utils.get_render_elements()
    if render_elements:
        # RenderElements parameter
        parameter_values.append(
            {"name": "RenderElements", "value": "true" if settings.render_elements else "false"}
        )

        # IgnoreRenderElements parameter
        parameter_values.append(
            {
                "name": "IgnoreRenderElements",
                "value": "true" if settings.ignore_render_elements else "false",
            }
        )

        # IgnoreRenderElementsByName parameter
        if settings.ignore_render_elements_by_name:
            # Convert list to comma-separated string for OpenJD
            ignore_names_str = ",".join(settings.ignore_render_elements_by_name)
            parameter_values.append(
                {"name": "IgnoreRenderElementsByName", "value": ignore_names_str}
            )
        elif any(elem.get("name") for elem in render_elements):
            # Add empty parameter if render elements exist but none are ignored
            parameter_values.append({"name": "IgnoreRenderElementsByName", "value": ""})

        # RenderElementOutputFilenames parameter
        if settings.render_element_output_filenames:
            # Convert list to comma-separated string for OpenJD
            output_filenames_str = ",".join(settings.render_element_output_filenames)
            parameter_values.append(
                {"name": "RenderElementOutputFilenames", "value": output_filenames_str}
            )
        elif any(elem.get("output_filename") for elem in render_elements):
            # Add empty parameter if render elements exist but no output filenames
            parameter_values.append({"name": "RenderElementOutputFilenames", "value": ""})

    return parameter_values


def _get_queue_parameters_for_bundle(
    settings: RenderSubmitterUISettings,
    parameter_values: list[dict[str, Any]],
    queue_parameters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Checks for any overlap between the job parameters we've defined and the queue parameters.
    Removes the deadline_cloud_for_3ds_max from the RezPackages if adaptor wheels are included.

    :param settings: a RenderSubmitterUISettings object containing the latest UI settings
    :param parameter_values: the job parameters we've defined
    :param queue_parameters: the settings from the shared job settings tab

    :raises: a DeadlineOperationError if there is overlap between the job parameters and the queue parameters.
    This is an error, as we weren't synchronizing the values between the two different tabs where they came from.
    """
    parameter_names = {param["name"] for param in parameter_values}
    queue_parameter_names = {param["name"] for param in queue_parameters}
    parameter_overlap = parameter_names.intersection(queue_parameter_names)
    if parameter_overlap:
        raise DeadlineOperationError(
            "The following queue parameters conflict with the "
            "Max job parameters:\n" + f"{', '.join(parameter_overlap)}"
        )

    # If we're overriding the adaptor with wheels, remove deadline_cloud_for_3ds_max from the RezPackages
    if settings.include_adaptor_wheels:
        conda_param: dict[str, str] = {}
        # Find the RezPackages parameter definition
        for param in queue_parameters:
            if param["name"] == "CondaPackages":
                conda_param = param
                break
        # Remove the deadline_cloud_for_3ds_max rez package
        if conda_param:
            conda_param["value"] = " ".join(
                pkg for pkg in conda_param["value"].split() if not pkg.startswith("3dsmax-openjd")
            )

    return queue_parameters


def _validate_render_elements_parameters(settings: RenderSubmitterUISettings) -> None:
    """
    Validates render elements parameter consistency to ensure settings are coherent.

    :param settings: a RenderSubmitterUISettings object containing the latest UI settings
    :raises DeadlineOperationError: if render elements parameters are inconsistent
    """
    # If render elements are disabled, ignore other settings
    if not settings.render_elements:
        return

    # If ignoring all render elements, ignore by name list should be empty or irrelevant
    if settings.ignore_render_elements and settings.ignore_render_elements_by_name:
        # This is not an error, but log a warning that ignore by name will be ignored
        import logging

        _logger = logging.getLogger(__name__)
        _logger.warning(
            "Both 'ignore all render elements' and 'ignore by name' are set. "
            "The 'ignore by name' list will be ignored since all render elements are being ignored."
        )

    # Validate that ignored render element names exist in the scene
    if settings.ignore_render_elements_by_name:
        try:
            invalid_names = settings.validate_render_element_names()
            if invalid_names:
                raise DeadlineOperationError(
                    f"The following render element names to ignore do not exist in the scene: "
                    f"{', '.join(invalid_names)}"
                )
        except Exception as e:
            # If validation fails, log warning but don't fail submission
            import logging

            _logger = logging.getLogger(__name__)
            _logger.warning(f"Could not validate render element names: {e}")

    # Validate render element output paths
    if settings.render_element_output_filenames:
        try:
            invalid_paths = settings.validate_render_element_paths()
            if invalid_paths:
                raise DeadlineOperationError(
                    f"The following render element output paths are invalid or inaccessible: "
                    f"{', '.join(invalid_paths)}"
                )
        except Exception as e:
            # If validation fails, log warning but don't fail submission
            import logging

            _logger = logging.getLogger(__name__)
            _logger.warning(f"Could not validate render element paths: {e}")


def _check_multiples(state_sets: list[StateSetData], type_: str) -> bool:
    """
    Checks if there are different values for the given type in a list of
    LayerData objects.

    :param state_sets: a list of LayerData objects representing the state sets
    that were send along for submission.
    :type state_sets: list[StateSetData]
    :param type_: the parameter in the LayerData class we want to check for
    multiples
    :type type_: str

    :returns: a boolean representing whether there were multiple values for
    the given type
    """
    if not hasattr(state_sets[0], type_):
        return False
    previous = getattr(state_sets[0], type_)
    for state_set in state_sets:
        if getattr(state_set, type_) != previous:
            return True
        previous = getattr(state_set, type_)
    return False
