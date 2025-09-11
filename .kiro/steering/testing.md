# 3dsMax Integration: From Zero to Hero

## Development Testing using Adaptor Directly

With the 3dsmax package, we can test the integration directly on any Windows machine by calling the adaptor directly, without setting up worker agent, to speed up development. 

For example, if you’re testing whether a job bundle works properly with your new changes to the adaptor:


1. Have 3dsMax installed on the Windows machine with the necessary licensing setup 
2. Make changes to the adaptor as necessary for development.
3. Build `deadline-cloud-for-3ds-max`.
4. Install your dev version of the adaptor. (Example Powershell command below)
    1. `& "C:\Program Files\Autodesk\3ds Max 2024\Python\python.exe" -m pip install C:\Users\rdp\workplace\deadline-cloud-for-3ds-max\dist\deadline_cloud_for_3ds_max-0.0.post35+g90db704.d20250116-py3-none-any.whl —force-reinstall —no-deps`
5. Install the submitter (if you want to create a new job bundle) using https://github.com/aws-deadline/deadline-cloud-for-3ds-max/blob/mainline/DEVELOPMENT.md.
6. Add these two folders to your computer's PATH env variable:
    1. The 3ds Max Python folder (usually found at `C:\Program Files\Autodesk\3ds Max 2024\Python`)
    2. The Python scripts folder (usually found at `C:\Users\``<your username>\AppData\Roaming\Python\Python310\Scripts`)
7. Also set your PYTHONPATH env variable to point to the 3ds Max Python folder.
8. Once you have the job bundle exported through the submitter or downloaded from elsewhere:
    1. Go into the `template.yaml` file
    2. Find the commands that start with `3dsmax-openjd daemon start` and `3dsmax-openjd daemon run` and combine the 2 commands without the `--connection-file` part, resolving variable references using the `parameter_values` file 
        1. An example resulting command in command prompt would be 
            `3dsmax-openjd run --init-data "{\"scene_file\": \"C:/Users/ryanliyt/Downloads/Shape/Shape/3DS Max/Shape.max\", \"state_set\": \"State01\", \"renderer\": \"Redshift_Renderer\", \"output_file_name\": \"State01_Shape\", \"render_layer\": \"masterLayer\", \"output_file_path\": \"C:/Users/ryanliyt/Downloads/T-Rex/T-Rex/3DS Max/\", \"output_file_format\": \".jpg\", \"image_width\": 1280, \"image_height\": 720}" --run-data "{\"frame\": 1, \"camera\": \"Camera001\"}"` 
9. Run this command in command prompt. You should see it working and if everything is correct, the render should complete within minutes.
    1. Note: if there are critical errors, the terminal command might not indicate an error. To debug, view the 3dsmax logs at `C:\Users\<your username>\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\Network` 

## Open Questions

* Hands-on: work through a github issue or dependabot PR?
* Looking for more info on how the adaptor keeps the DCC open across sessions? What does that look like/how does that work?
* Logs as events? Looks like something we need to keep on the lookout for in case the DCC’s change their log.
    * Yes, we’ve seem something very similar when supporting 3DSMaxBatch
    * Also support for other languages. Seems like we’d also have some challenges getting the adaptor working for non-english language versions of installed 3DSMax.
* Known issue with launching a windows CMF fleet following the steps here: [Window CMF Worker Setup](https://quip-amazon.com/VKfoAnxqG6N4). The ami launches a Linux instance.
* What do we need to get a 3DSMaxSubmitter installer?
* What’s the difference between “Manual Installation” and “Install for Development”?

## References

* [Integration Handoff - Maya/3ds Max](https://quip-amazon.com/TGuQA2oiP1TZ)
* [3dsMax: Integration Security Reviews for Deadline Cloud](https://quip-amazon.com/L7RYAe4dHmaJ)
* https://github.com/aws-deadline/deadline-cloud-for-3ds-max
* [Window CMF Worker Setup](https://quip-amazon.com/VKfoAnxqG6N4)

