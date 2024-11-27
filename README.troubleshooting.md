## Issues we've run into and how we have solved them

### Issue 1
**Error message (while running an OB flow):**

```commandline
nothing provides requested google-cloud-secret-manager >=2.10.0
    nothing provides __glibc >=2.17 needed by libgcc-ng-11.2.0-h1234567_0
```

**Solution:**

Outerbounds (actually Metaflow) expects conda-forge to be the top-prioritized conda channel on the machine, and Sen's was defaults . There are three options for fixing this:
- Option 1 (affects whole machine, problem if different projects use conda differently): change the .condarc file to have - conda-forge first in the channels list, above anything else like - defaults
- Option 2 (affects only the specific command you're running): Add CONDA_OVERRIDE_GLIBC=2.17 CONDA_CHANNELS=conda-forge CONDA_PKGS_DIRS=.conda to the front of your my_flow.py run  command
- Option 3 (avoids machine issues): Run the flow from a remote workstation. This was OB's suggestion but I'm not in love with it due to the limitation on experimenting with the allowances of perimeter permissions outside of flows in workstations.

### Issue 2
**Error message (while running an OB flow):**

```commandline
2024-11-07 13:04:32.537 [183/generate_message/641 (pid 67223)] [pod t-67184c43-ssvz7-rpt76]   File "/usr/local/lib/python3.9/runpy.py", line 87, in _run_code
2024-11-07 13:04:32.537 [183/generate_message/641 (pid 67223)] [pod t-67184c43-ssvz7-rpt76]     exec(code, run_globals)
2024-11-07 13:04:32.537 [183/generate_message/641 (pid 67223)] [pod t-67184c43-ssvz7-rpt76]   File "/metaflow/metaflow/plugins/pypi/bootstrap.py", line 69, in <module>
2024-11-07 13:04:32.538 [183/generate_message/641 (pid 67223)] [pod t-67184c43-ssvz7-rpt76]     env = json.load(f)[id_][architecture]
2024-11-07 13:04:32.538 [183/generate_message/641 (pid 67223)] [pod t-67184c43-ssvz7-rpt76] KeyError: 'e0b9a5a0b2a44d2'```
```

**Solution:**

Switch the virtual environment to using Python 3.10.8. Anything 3.11+ is prone to producing this in conjunction with the subdependencies of OB.

### Issue 3: `@pypi` does not support source distributions
**Error message (while running an OB flow):**

```commandline
Note that @pypi does not currently support source distributions
```

**Solution:**

This error happens when your Flow depends on a package that is only available as a [source distribution](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#source-distributions) which [`@pypi` decorator doesn't support](https://docs.metaflow.org/api/step-decorators/pypi). The way to resolve this is:
- Create a custom docker image with all of your Flow's dependencies, push that up on a registry (see [README.Docker.md](./src/mozmlops/templates/README.Docker.md) for reference) and then pull it down via the `image` argument of `@kubernetes` decorator. The caveat is that custom docker images are not yet supported on NVIDIA cloud (i.e. `@nvidia` decorator).

### Issue 4: Out of Memory error (Task finished with exit code 137)
**Error message (while running an OB flow):**

```commandline
2024-11-12 09:19:58.406 [191/generate_message/665 (pid 17393)] [pod t-c542580d-wjvhd-nm6vt] Task finished with exit code 137.
2024-11-12 09:20:02.001 Workflow failed.
2024-11-12 09:20:02.001 Terminating 1 active tasks...
2024-11-12 09:20:02.001 [191/generate_message/665 (pid 17393)] [KILLED BY ORCHESTRATOR]
2024-11-12 09:20:02.001 [191/generate_message/665 (pid 17393)] [KILLED BY ORCHESTRATOR]
2024-11-12 09:20:02.001 Flushing logs...
    Data store error:
    No completed attempts of the task was found for task 'TemplateFlow/191/generate_message/665'
```

**Solution:**

This error happens when a step in your Flow requires more memory than:
1. What is allocated to it, OR
2. What is available in the perimeter where your Flow is running i.e. _perimeter memory limit_

The way to resolve it is:
- Try increasing the [memory](https://docs.metaflow.org/api/step-decorators/kubernetes#kubernetes) allocation for the failing step and re-run the Flow. Please note that you can increase this memory to a maximum of _perimeter memory limit_. Please reach out to MLOps team to find this limit.
- If the above step doesn't resolve the issue, reach out to MLOps team for help wrt increasing the _perimeter memory limit_ and then follow previous step again.


### Issue 5: Step annotated with `@pypi` (or `@conda`) decorator as well as `@kubernetes` decorator that specifies the [custom image](https://docs.metaflow.org/api/step-decorators/kubernetes#kubernetes) ignores the custom image when Flow is executed with `--environment pypi` (or `--environment conda`) on CLI

**Probable Error message (while running an OB flow):**

```commandline
ModuleNotFoundError: No module named XXX
```

**Solution:**
The reason of the failure and the way to fix is provided in the [docs](https://docs.metaflow.org/scaling/dependencies/libraries#disabling-environments).

- Set `@pypi(disabled=True)` (or `@conda(disabled=True)`) at the step that should use the custom image
