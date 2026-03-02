-- use this file as your Hammerspoon init.lua

hs.alert.show("Hammerspoon config loaded!")

-- Guard so synthetic keystrokes don't re-trigger snippets.
local injecting = false

-- Types multiline text without touching clipboard.
local function typeMultiline(s)
  local i = 1
  while i <= #s do
    local j = s:find("\n", i, true)
    if j then
      local line = s:sub(i, j - 1)
      if #line > 0 then hs.eventtap.keyStrokes(line) end
      hs.eventtap.keyStroke({}, "return", 0)
      i = j + 1
    else
      local rest = s:sub(i)
      if #rest > 0 then hs.eventtap.keyStrokes(rest) end
      break
    end
  end
end

local snippets = {
  [";;chat1"]   = "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -o addopts='' tests/chat_server/level_1_tests.py",
  [";;chat2"]   = "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -o addopts='' tests/chat_server/level_2_tests.py",
  [";;chat3"]   = "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -o addopts='' tests/chat_server/level_3_tests.py",
  [";;chat4"]   = "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -o addopts='' tests/chat_server/level_4_tests.py",
  [";;chatadv"] = "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -o addopts='' tests/chat_server/adversarial_tests.py",
  [";;chatall"] = "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q -o addopts='' tests/chat_server",
}

-- Rolling buffer of recent typed chars to detect triggers.
local buffer = ""

local tap = hs.eventtap.new({ hs.eventtap.event.types.keyDown }, function(e)
  if injecting then return false end

  local f = e:getFlags()
  if f.cmd or f.alt or f.ctrl then return false end

  local keyCode = e:getKeyCode()
  local char = e:getCharacters()

  if keyCode == hs.keycodes.map.delete then
    buffer = buffer:sub(1, -2)
    return false
  end

  if keyCode == hs.keycodes.map.space
      or keyCode == hs.keycodes.map["return"]
      or keyCode == hs.keycodes.map.tab
      or keyCode == hs.keycodes.map.escape then
    buffer = ""
    return false
  end

  if char and #char > 0 then
    buffer = buffer .. char
    if #buffer > 80 then buffer = buffer:sub(-80) end

    for trig, out in pairs(snippets) do
      if #buffer >= #trig and buffer:sub(-#trig) == trig then
        injecting = true
        hs.timer.doAfter(0, function()
          for _ = 1, #trig do hs.eventtap.keyStroke({}, "delete", 0) end
          typeMultiline(out)
          hs.timer.doAfter(0.05, function() injecting = false end)
        end)
        buffer = ""
        break
      end
    end
  end

  return false
end)

tap:start()
hs.alert.show("Hotstrings: ;;chat1 ;;chat2 ;;chat3 ;;chat4 ;;chatadv ;;chatall")
