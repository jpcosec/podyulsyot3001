local function latex_escape(value)
  if not value then
    return ""
  end

  local escaped = value
  escaped = escaped:gsub("\\", "\\textbackslash{}")
  escaped = escaped:gsub("([#%%&{}_])", "\\%1")
  escaped = escaped:gsub("%$", "\\$")
  escaped = escaped:gsub("%*", "\\atswhite{*}")
  return escaped
end

local function attr(el, ...)
  local names = { ... }
  for _, name in ipairs(names) do
    local value = el.attributes[name]
    if value and value ~= "" then
      return value
    end
  end
  return ""
end

local function inlines_to_latex(inlines)
  local parts = {}
  for _, inline in ipairs(inlines) do
    if inline.t == "Str" then
      table.insert(parts, latex_escape(inline.text))
    elseif inline.t == "Space" then
      table.insert(parts, " ")
    elseif inline.t == "SoftBreak" or inline.t == "LineBreak" then
      table.insert(parts, " ")
    elseif inline.t == "Emph" then
      table.insert(parts, "\\emph{" .. inlines_to_latex(inline.content) .. "}")
    elseif inline.t == "Strong" then
      table.insert(parts, "\\textbf{" .. inlines_to_latex(inline.content) .. "}")
    elseif inline.t == "Code" then
      table.insert(parts, "\\texttt{" .. latex_escape(inline.text) .. "}")
    else
      table.insert(parts, latex_escape(pandoc.utils.stringify(inline)))
    end
  end
  return table.concat(parts)
end

local function blocks_to_latex(blocks)
  if #blocks == 0 then
    return ""
  end

  local parts = {}
  for _, block in ipairs(blocks) do
    if block.t == "BulletList" then
      table.insert(parts, "\\begin{itemize}\n")
      for _, item in ipairs(block.content) do
        local item_parts = {}
        for _, item_block in ipairs(item) do
          if item_block.t == "Plain" or item_block.t == "Para" then
            table.insert(item_parts, inlines_to_latex(item_block.content))
          end
        end
        table.insert(parts, "\\item " .. table.concat(item_parts, " ") .. "\n")
      end
      table.insert(parts, "\\end{itemize}\n")
    elseif block.t == "Para" or block.t == "Plain" then
      table.insert(parts, inlines_to_latex(block.content) .. "\n\n")
    end
  end

  return table.concat(parts)
end

function Div(el)
  if el.classes[1] == "job" then
    local role = latex_escape(attr(el, "role"))
    local org = latex_escape(attr(el, "org"))
    local dates = latex_escape(attr(el, "dates"))
    local location = latex_escape(attr(el, "location", "loc"))
    local body = blocks_to_latex(el.content)

    return pandoc.RawBlock(
      "latex",
      string.format("\\cvjob{%s}{%s}{%s}{%s}{%s}", dates, role, org, location, body)
    )
  end

  if el.classes[1] == "edu" or el.classes[1] == "education" then
    local degree = latex_escape(attr(el, "degree"))
    local specialization = latex_escape(attr(el, "specialization"))
    local institution = latex_escape(attr(el, "inst", "institution"))
    local dates = latex_escape(attr(el, "dates"))
    local location = latex_escape(attr(el, "loc", "location"))
    local body = blocks_to_latex(el.content)

    return pandoc.RawBlock(
      "latex",
      string.format(
        "\\cvedu{%s}{%s}{%s}{%s}{%s}{%s}",
        dates,
        degree,
        specialization,
        institution,
        location,
        body
      )
    )
  end

  return el
end
