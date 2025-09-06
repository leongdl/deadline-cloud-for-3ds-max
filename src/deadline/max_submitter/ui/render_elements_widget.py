# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Enhanced Render Elements Widget for 3ds Max Deadline Cloud Submitter.

This widget provides comprehensive render elements controls matching Deadline 10's
feature set, including advanced path management and V-Ray integration.
"""

import logging

from qtpy.QtCore import Qt, Signal  # type: ignore
from qtpy.QtWidgets import (  # type: ignore
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from deadline.max_submitter.utilities import max_utils

_logger = logging.getLogger(__name__)


class EnhancedRenderElementsWidget(QWidget):
    """
    Enhanced render elements widget with comprehensive Deadline 10 feature parity.

    This widget extends the basic render elements support with advanced path management,
    V-Ray integration, and comprehensive validation feedback.
    """

    # Signals for communicating changes to parent
    settings_changed = Signal()
    validation_changed = Signal(list)  # Emits list of validation warnings

    def __init__(self, initial_settings, parent=None):
        super().__init__(parent=parent)
        self.settings = initial_settings
        self._build_enhanced_render_elements_ui()
        self._connect_signals()
        self._refresh_detected_elements()

    def _build_enhanced_render_elements_ui(self):
        """
        Build the enhanced render elements UI with comprehensive controls.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Basic Render Elements Section
        self._build_basic_render_elements_section(main_layout)

        # Advanced Path Management Section
        self._build_path_management_section(main_layout)

        # V-Ray Integration Section
        self._build_vray_integration_section(main_layout)

        # Detected Elements and Validation Section
        self._build_detection_validation_section(main_layout)

    def _build_basic_render_elements_section(self, parent_layout):
        """
        Build the basic render elements controls section.
        """
        basic_group = QGroupBox("Render Elements")
        basic_layout = QGridLayout(basic_group)
        parent_layout.addWidget(basic_group)

        # Output Render Elements checkbox
        self.render_elements_checkbox = QCheckBox("Output Render Elements")
        self.render_elements_checkbox.setToolTip(
            "Enable or disable render elements output during rendering"
        )
        basic_layout.addWidget(self.render_elements_checkbox, 0, 0)

        # Ignore All Render Elements checkbox
        self.ignore_render_elements_checkbox = QCheckBox("Ignore All Render Elements")
        self.ignore_render_elements_checkbox.setToolTip(
            "Ignore all render elements in the scene, overriding individual settings"
        )
        basic_layout.addWidget(self.ignore_render_elements_checkbox, 0, 1)

        # Ignore by Name section
        ignore_label = QLabel("Ignore Render Elements by Name:")
        basic_layout.addWidget(ignore_label, 1, 0, 1, 2)

        self.ignore_elements_list = QListWidget()
        self.ignore_elements_list.setMaximumHeight(100)
        self.ignore_elements_list.setToolTip(
            "List of render element names to ignore during rendering"
        )
        basic_layout.addWidget(self.ignore_elements_list, 2, 0, 1, 2)

        # Ignore list management buttons
        ignore_buttons_layout = QHBoxLayout()
        self.add_ignore_btn = QPushButton("Add Element")
        self.add_ignore_btn.setToolTip("Add selected detected element to ignore list")
        self.remove_ignore_btn = QPushButton("Remove Selected")
        self.remove_ignore_btn.setToolTip("Remove selected element from ignore list")

        ignore_buttons_layout.addWidget(self.add_ignore_btn)
        ignore_buttons_layout.addWidget(self.remove_ignore_btn)
        ignore_buttons_layout.addStretch()

        ignore_buttons_widget = QWidget()
        ignore_buttons_widget.setLayout(ignore_buttons_layout)
        basic_layout.addWidget(ignore_buttons_widget, 3, 0, 1, 2)

    def _build_path_management_section(self, parent_layout):
        """
        Build the advanced path management controls section.
        """
        path_group = QGroupBox("Render Element Path Management")
        path_layout = QGridLayout(path_group)
        parent_layout.addWidget(path_group)

        # Update paths checkbox
        self.update_paths_checkbox = QCheckBox("Update Render Element Paths")
        self.update_paths_checkbox.setToolTip(
            "Automatically update render element output paths based on naming settings"
        )
        path_layout.addWidget(self.update_paths_checkbox, 0, 0)

        # Update filenames checkbox
        self.update_filenames_checkbox = QCheckBox("Also Update Render Element Filenames")
        self.update_filenames_checkbox.setToolTip(
            "Update both paths and filenames when path updates are enabled"
        )
        path_layout.addWidget(self.update_filenames_checkbox, 0, 1)

        # Path naming options
        path_naming_label = QLabel("Path Naming Options:")
        path_layout.addWidget(path_naming_label, 1, 0, 1, 2)

        self.include_name_in_path_checkbox = QCheckBox("Include Render Element Name in Path")
        self.include_name_in_path_checkbox.setToolTip(
            "Add render element name as subdirectory in output path"
        )
        path_layout.addWidget(self.include_name_in_path_checkbox, 2, 0)

        self.include_type_in_path_checkbox = QCheckBox("Include Render Element Type in Path")
        self.include_type_in_path_checkbox.setToolTip(
            "Add render element type as subdirectory in output path"
        )
        path_layout.addWidget(self.include_type_in_path_checkbox, 2, 1)

        # Filename naming options
        filename_naming_label = QLabel("Filename Naming Options:")
        path_layout.addWidget(filename_naming_label, 3, 0, 1, 2)

        self.include_name_in_filename_checkbox = QCheckBox(
            "Include Render Element Name in Filename"
        )
        self.include_name_in_filename_checkbox.setToolTip(
            "Add render element name to output filename"
        )
        path_layout.addWidget(self.include_name_in_filename_checkbox, 4, 0)

        self.include_type_in_filename_checkbox = QCheckBox(
            "Include Render Element Type in Filename"
        )
        self.include_type_in_filename_checkbox.setToolTip(
            "Add render element type to output filename"
        )
        path_layout.addWidget(self.include_type_in_filename_checkbox, 4, 1)

        # State management options
        state_label = QLabel("State Management:")
        path_layout.addWidget(state_label, 5, 0, 1, 2)

        self.permanent_changes_checkbox = QCheckBox("Make Permanent Changes to Scene")
        self.permanent_changes_checkbox.setToolTip(
            "Apply render element changes permanently to the scene file"
        )
        path_layout.addWidget(self.permanent_changes_checkbox, 6, 0)

        self.rebuild_elements_checkbox = QCheckBox("Rebuild Render Elements if Needed")
        self.rebuild_elements_checkbox.setToolTip(
            "Automatically rebuild render elements if configuration issues are detected"
        )
        path_layout.addWidget(self.rebuild_elements_checkbox, 6, 1)

    def _build_vray_integration_section(self, parent_layout):
        """
        Build the V-Ray specific integration controls section.
        """
        vray_group = QGroupBox("V-Ray Integration")
        vray_layout = QGridLayout(vray_group)
        parent_layout.addWidget(vray_group)

        self.vray_vfb_control_checkbox = QCheckBox("Control V-Ray VFB for Render Elements")
        self.vray_vfb_control_checkbox.setToolTip(
            "Automatically control V-Ray VFB settings for render elements during rendering"
        )
        vray_layout.addWidget(self.vray_vfb_control_checkbox, 0, 0)

        self.vray_split_buffer_checkbox = QCheckBox("Support V-Ray Split Buffer")
        self.vray_split_buffer_checkbox.setToolTip(
            "Enable V-Ray split buffer support for render elements"
        )
        vray_layout.addWidget(self.vray_split_buffer_checkbox, 0, 1)

        self.vray_separate_folders_checkbox = QCheckBox("Use Separate Folders for V-Ray Elements")
        self.vray_separate_folders_checkbox.setToolTip(
            "Create separate folders for different V-Ray render element types"
        )
        vray_layout.addWidget(self.vray_separate_folders_checkbox, 1, 0, 1, 2)

    def _build_detection_validation_section(self, parent_layout):
        """
        Build the render elements detection and validation section.
        """
        detection_group = QGroupBox("Detected Render Elements")
        detection_layout = QVBoxLayout(detection_group)
        parent_layout.addWidget(detection_group)

        # Detected elements list
        self.detected_elements_list = QListWidget()
        self.detected_elements_list.setMaximumHeight(150)
        self.detected_elements_list.setToolTip(
            "List of render elements detected in the current scene"
        )
        detection_layout.addWidget(self.detected_elements_list)

        # Refresh button
        self.refresh_elements_btn = QPushButton("Refresh Detected Elements")
        self.refresh_elements_btn.setToolTip("Refresh the list of detected render elements")
        detection_layout.addWidget(self.refresh_elements_btn)

        # Validation feedback
        self.validation_feedback_label = QLabel("")
        self.validation_feedback_label.setStyleSheet("color: red;")
        self.validation_feedback_label.setWordWrap(True)
        self.validation_feedback_label.setMinimumHeight(40)
        detection_layout.addWidget(self.validation_feedback_label)

    def _connect_signals(self):
        """
        Connect all widget signals to their respective handlers.
        """
        # Basic controls
        self.render_elements_checkbox.stateChanged.connect(self._on_render_elements_changed)
        self.ignore_render_elements_checkbox.stateChanged.connect(self._on_ignore_all_changed)

        # Ignore list management
        self.add_ignore_btn.clicked.connect(self._add_ignore_element)
        self.remove_ignore_btn.clicked.connect(self._remove_ignore_element)

        # Path management controls
        self.update_paths_checkbox.stateChanged.connect(self._on_settings_changed)
        self.update_filenames_checkbox.stateChanged.connect(self._on_settings_changed)
        self.include_name_in_path_checkbox.stateChanged.connect(self._on_settings_changed)
        self.include_type_in_path_checkbox.stateChanged.connect(self._on_settings_changed)
        self.include_name_in_filename_checkbox.stateChanged.connect(self._on_settings_changed)
        self.include_type_in_filename_checkbox.stateChanged.connect(self._on_settings_changed)
        self.permanent_changes_checkbox.stateChanged.connect(self._on_settings_changed)
        self.rebuild_elements_checkbox.stateChanged.connect(self._on_settings_changed)

        # V-Ray controls
        self.vray_vfb_control_checkbox.stateChanged.connect(self._on_settings_changed)
        self.vray_split_buffer_checkbox.stateChanged.connect(self._on_settings_changed)
        self.vray_separate_folders_checkbox.stateChanged.connect(self._on_settings_changed)

        # Detection and validation
        self.refresh_elements_btn.clicked.connect(self._refresh_detected_elements)

    def _on_render_elements_changed(self, state):
        """
        Handle changes to the main render elements checkbox.
        """
        enabled = Qt.CheckState(state) == Qt.Checked

        # Enable/disable dependent controls
        self.ignore_render_elements_checkbox.setEnabled(enabled)
        self.ignore_elements_list.setEnabled(enabled)
        self.add_ignore_btn.setEnabled(enabled)
        self.remove_ignore_btn.setEnabled(enabled)
        self.detected_elements_list.setEnabled(enabled)
        self.refresh_elements_btn.setEnabled(enabled)

        # Enable/disable path management controls
        self.update_paths_checkbox.setEnabled(enabled)
        self.update_filenames_checkbox.setEnabled(enabled)
        self.include_name_in_path_checkbox.setEnabled(enabled)
        self.include_type_in_path_checkbox.setEnabled(enabled)
        self.include_name_in_filename_checkbox.setEnabled(enabled)
        self.include_type_in_filename_checkbox.setEnabled(enabled)
        self.permanent_changes_checkbox.setEnabled(enabled)
        self.rebuild_elements_checkbox.setEnabled(enabled)

        # Enable/disable V-Ray controls
        self.vray_vfb_control_checkbox.setEnabled(enabled)
        self.vray_split_buffer_checkbox.setEnabled(enabled)
        self.vray_separate_folders_checkbox.setEnabled(enabled)

        self._on_settings_changed()

    def _on_ignore_all_changed(self, state):
        """
        Handle changes to the ignore all render elements checkbox.
        """
        ignore_all = Qt.CheckState(state) == Qt.Checked
        elements_enabled = self.render_elements_checkbox.isChecked()

        # Disable individual ignore controls when ignoring all
        self.ignore_elements_list.setEnabled(not ignore_all and elements_enabled)
        self.add_ignore_btn.setEnabled(not ignore_all and elements_enabled)
        self.remove_ignore_btn.setEnabled(not ignore_all and elements_enabled)

        self._on_settings_changed()

    def _on_settings_changed(self):
        """
        Handle any settings change and trigger validation.
        """
        self._validate_render_elements()
        self.settings_changed.emit()

    def _add_ignore_element(self):
        """
        Add a render element name to the ignore list.
        """
        current_item = self.detected_elements_list.currentItem()
        if not current_item:
            return

        # Extract element name from display text
        element_name = current_item.text().split(" - ")[0]

        # Check if already in ignore list
        for i in range(self.ignore_elements_list.count()):
            if self.ignore_elements_list.item(i).text() == element_name:
                return  # Already in list

        # Add to ignore list
        self.ignore_elements_list.addItem(element_name)
        self._on_settings_changed()

    def _remove_ignore_element(self):
        """
        Remove selected render element name from the ignore list.
        """
        current_row = self.ignore_elements_list.currentRow()
        if current_row >= 0:
            self.ignore_elements_list.takeItem(current_row)
            self._on_settings_changed()

    def _refresh_detected_elements(self):
        """
        Refresh the list of detected render elements from the scene.
        """
        self.detected_elements_list.clear()

        try:
            render_elements = max_utils.get_render_elements()

            if not render_elements:
                item = QListWidgetItem("No render elements detected in scene")
                item.setToolTip("No render elements found in the current 3ds Max scene")
                self.detected_elements_list.addItem(item)
                return

            for element in render_elements:
                name = element.get("name", "Unknown")
                element_type = element.get("type", "Unknown")
                enabled = element.get("enabled", True)
                has_output = element.get("has_output_path", False)
                output_filename = element.get("output_filename", "")
                vray_vfb = element.get("vray_vfb", False)

                # Create status indicators
                status_parts = []
                if not enabled:
                    status_parts.append("DISABLED")
                if not has_output:
                    status_parts.append("NO OUTPUT PATH")
                if vray_vfb:
                    status_parts.append("V-RAY VFB")

                status_text = f" ({', '.join(status_parts)})" if status_parts else ""
                display_text = f"{name} - {element_type}{status_text}"

                item = QListWidgetItem(display_text)
                tooltip = (
                    f"Name: {name}\n"
                    f"Type: {element_type}\n"
                    f"Enabled: {enabled}\n"
                    f"V-Ray VFB: {vray_vfb}\n"
                    f"Output: {output_filename or 'Not set'}"
                )
                item.setToolTip(tooltip)
                self.detected_elements_list.addItem(item)

        except Exception as e:
            _logger.error(f"Error refreshing render elements: {e}")
            item = QListWidgetItem(f"Error detecting render elements: {e}")
            self.detected_elements_list.addItem(item)

        self._validate_render_elements()

    def _validate_render_elements(self):
        """
        Validate render elements settings and show feedback.
        """
        feedback_messages = []

        try:
            # Get current render elements
            render_elements = max_utils.get_render_elements()

            # Validate paths
            path_warnings = max_utils.validate_render_element_paths(render_elements)
            feedback_messages.extend(path_warnings)

            # Validate ignore list
            ignore_names = []
            for i in range(self.ignore_elements_list.count()):
                ignore_names.append(self.ignore_elements_list.item(i).text())

            if ignore_names:
                scene_element_names = [elem.get("name", "") for elem in render_elements]
                invalid_names = [name for name in ignore_names if name not in scene_element_names]

                for invalid_name in invalid_names:
                    feedback_messages.append(f"Ignored element '{invalid_name}' not found in scene")

            # Validate configuration consistency
            settings_dict = self.get_settings_dict()
            config_warnings = max_utils.validate_render_element_configuration(
                render_elements, settings_dict
            )
            feedback_messages.extend(config_warnings)

        except Exception as e:
            _logger.error(f"Error validating render elements: {e}")
            feedback_messages.append(f"Error validating render elements: {e}")

        # Display feedback
        if feedback_messages:
            self.validation_feedback_label.setText("\n".join(feedback_messages))
        else:
            self.validation_feedback_label.setText("✓ Render elements configuration is valid")
            self.validation_feedback_label.setStyleSheet("color: green;")

        # Emit validation signal
        self.validation_changed.emit(feedback_messages)

    def get_settings_dict(self) -> dict:
        """
        Get current settings as a dictionary for validation.

        :returns: Dictionary containing current widget settings
        :return_type: dict
        """
        return {
            "render_elements": self.render_elements_checkbox.isChecked(),
            "ignore_render_elements": self.ignore_render_elements_checkbox.isChecked(),
            "ignore_render_elements_by_name": [
                self.ignore_elements_list.item(i).text()
                for i in range(self.ignore_elements_list.count())
            ],
            "render_elements_update_paths": self.update_paths_checkbox.isChecked(),
            "render_elements_update_filenames": self.update_filenames_checkbox.isChecked(),
            "render_elements_include_name_in_path": self.include_name_in_path_checkbox.isChecked(),
            "render_elements_include_type_in_path": self.include_type_in_path_checkbox.isChecked(),
            "render_elements_include_name_in_filename": self.include_name_in_filename_checkbox.isChecked(),
            "render_elements_include_type_in_filename": self.include_type_in_filename_checkbox.isChecked(),
            "render_elements_permanent_changes": self.permanent_changes_checkbox.isChecked(),
            "rebuild_render_elements": self.rebuild_elements_checkbox.isChecked(),
            "vray_render_elements_vfb_control": self.vray_vfb_control_checkbox.isChecked(),
            "vray_split_buffer_support": self.vray_split_buffer_checkbox.isChecked(),
            "vray_separate_folders": self.vray_separate_folders_checkbox.isChecked(),
        }

    def update_from_settings(self, settings):
        """
        Update widget state from settings object.

        :param settings: Settings object containing render elements configuration
        """
        # Block signals during update to prevent recursive updates
        self.blockSignals(True)

        try:
            # Basic settings
            self.render_elements_checkbox.setChecked(getattr(settings, "render_elements", True))
            self.ignore_render_elements_checkbox.setChecked(
                getattr(settings, "ignore_render_elements", False)
            )

            # Update ignore list
            self.ignore_elements_list.clear()
            ignore_names = getattr(settings, "ignore_render_elements_by_name", [])
            for name in ignore_names:
                self.ignore_elements_list.addItem(name)

            # Path management settings
            self.update_paths_checkbox.setChecked(
                getattr(settings, "render_elements_update_paths", True)
            )
            self.update_filenames_checkbox.setChecked(
                getattr(settings, "render_elements_update_filenames", True)
            )
            self.include_name_in_path_checkbox.setChecked(
                getattr(settings, "render_elements_include_name_in_path", True)
            )
            self.include_type_in_path_checkbox.setChecked(
                getattr(settings, "render_elements_include_type_in_path", False)
            )
            self.include_name_in_filename_checkbox.setChecked(
                getattr(settings, "render_elements_include_name_in_filename", True)
            )
            self.include_type_in_filename_checkbox.setChecked(
                getattr(settings, "render_elements_include_type_in_filename", False)
            )
            self.permanent_changes_checkbox.setChecked(
                getattr(settings, "render_elements_permanent_changes", True)
            )
            self.rebuild_elements_checkbox.setChecked(
                getattr(settings, "rebuild_render_elements", True)
            )

            # V-Ray settings
            self.vray_vfb_control_checkbox.setChecked(
                getattr(settings, "vray_render_elements_vfb_control", True)
            )
            self.vray_split_buffer_checkbox.setChecked(
                getattr(settings, "vray_split_buffer_support", True)
            )
            self.vray_separate_folders_checkbox.setChecked(
                getattr(settings, "vray_separate_folders", False)
            )

            # Trigger state updates
            self._on_render_elements_changed(
                Qt.Checked if self.render_elements_checkbox.isChecked() else Qt.Unchecked
            )
            self._on_ignore_all_changed(
                Qt.Checked if self.ignore_render_elements_checkbox.isChecked() else Qt.Unchecked
            )

        finally:
            self.blockSignals(False)

        # Refresh and validate
        self._refresh_detected_elements()

    def update_settings_from_widget(self, settings):
        """
        Update settings object from current widget state.

        :param settings: Settings object to update
        """
        # Basic settings
        settings.render_elements = self.render_elements_checkbox.isChecked()
        settings.ignore_render_elements = self.ignore_render_elements_checkbox.isChecked()

        # Update ignore list
        ignore_names = []
        for i in range(self.ignore_elements_list.count()):
            ignore_names.append(self.ignore_elements_list.item(i).text())
        settings.ignore_render_elements_by_name = ignore_names

        # Path management settings
        settings.render_elements_update_paths = self.update_paths_checkbox.isChecked()
        settings.render_elements_update_filenames = self.update_filenames_checkbox.isChecked()
        settings.render_elements_include_name_in_path = (
            self.include_name_in_path_checkbox.isChecked()
        )
        settings.render_elements_include_type_in_path = (
            self.include_type_in_path_checkbox.isChecked()
        )
        settings.render_elements_include_name_in_filename = (
            self.include_name_in_filename_checkbox.isChecked()
        )
        settings.render_elements_include_type_in_filename = (
            self.include_type_in_filename_checkbox.isChecked()
        )
        settings.render_elements_permanent_changes = self.permanent_changes_checkbox.isChecked()
        settings.rebuild_render_elements = self.rebuild_elements_checkbox.isChecked()

        # V-Ray settings
        settings.vray_render_elements_vfb_control = self.vray_vfb_control_checkbox.isChecked()
        settings.vray_split_buffer_support = self.vray_split_buffer_checkbox.isChecked()
        settings.vray_separate_folders = self.vray_separate_folders_checkbox.isChecked()
