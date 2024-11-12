## Issues we've run into and how we have solved them

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
