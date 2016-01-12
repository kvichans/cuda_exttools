Plugin for CudaText.
Allows to call external programs in CudaText.
Adds menu "Tools" (near "Plugins") with commands: 
    Config (customize tools),
    Run lexer main tool (analog of SublimeText's command "Build"), 
    Tool1...ToolN (items appear after tools are configured).

Config file is settings/exttools.json.

Details:
- "Shell command" option must be checked for tools which you want to run via OS-shell: 
  on Windows it's commands of cmd.exe. On Linux this opt usually not needed.
- If lexer(s) assigned to a tool, tool can be called only when these lexers active. 
- "Patterns" allow to parse output lines by regex, and find in these lines: 
  filename, line number, column number. If line parsed OK, you can jump to found
  line number and file by clicking in Output panel.


Author: A.Kvichanskiy (kvichans at forum/github)
License: MIT
