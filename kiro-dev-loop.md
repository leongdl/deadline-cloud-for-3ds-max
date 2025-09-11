# Kiro Development Loop: Fix, Build, Test Iteration

## Quick Development Workflow for 3ds Max Adaptor

### 1. Identify Issue
- Run test script to reproduce the bug
- Analyze error messages and logs
- Locate the problematic code

### 2. Make Code Changes
- Edit the source files in `src/deadline/max_adaptor/` or `src/deadline/max_submitter/`
- Use Kiro's file editing tools to make precise changes
- Focus on minimal, targeted fixes

### 3. Format and Build Updated Package
```powershell
hatch run fmt
hatch build
```
- `hatch run fmt` formats code according to project standards
- `hatch build` creates new wheel in `dist/` directory
- Note the new version number (e.g., `deadline_cloud_for_3ds_max-0.1.5.post31+g764700157-py3-none-any.whl`)

### 4. Test with Updated Package
```powershell
.\test-3dsmax-openjd.ps1 -WheelPath "dist\deadline_cloud_for_3ds_max-0.1.5.post31+g764700157-py3-none-any.whl" -JobBundleDir "render_element_bundle" -Verbose
```

### 5. Verify Results
- Check for successful completion (exit code 0)
- Review output logs for error resolution
- Confirm expected behavior changes
- Look for new warnings/validation messages

### 6. Iterate if Needed
- If issues remain, return to step 2
- For subsequent tests, use `-SkipInstall` flag for faster iteration:
```powershell
.\test-3dsmax-openjd.ps1 -WheelPath "dist\latest.whl" -JobBundleDir "render_element_bundle" -SkipInstall -Verbose
```

## Key Benefits of This Workflow

- **Fast Feedback**: Complete cycle in ~2-3 minutes
- **Isolated Testing**: Direct adaptor testing without full worker setup
- **Real Environment**: Uses actual 3ds Max installation
- **Comprehensive Logging**: Full visibility into adaptor behavior
- **Flexible**: Works with any job bundle for different test scenarios

## Test Script Features

- **Environment Setup**: Automatically configures Python paths and environment variables
- **Template Processing**: Extracts and substitutes parameters from job bundles
- **Error Detection**: Captures and displays both stdout and stderr
- **Performance Tracking**: Times execution for performance monitoring
- **Log Integration**: Points to 3ds Max logs for deeper debugging

## Best Practices

1. **Always format before building** - `hatch run fmt` ensures code follows project standards
2. **Always build before testing** - Ensures latest changes are included
3. **Use verbose mode** - Provides detailed execution information
4. **Check both success and failure cases** - Verify error handling works correctly
5. **Test with different job bundles** - Ensure changes work across scenarios
6. **Document fixes** - Create fix summaries for future reference