# C4A-Script Reference

Official reference: https://docs.crawl4ai.com/api/c4a-script-reference/

## Command Syntax Summary

### Navigation
```
GO <url>
RELOAD
BACK
FORWARD
```

### Wait
```
WAIT <seconds>
WAIT `<selector>` <timeout>
WAIT "<text>" <timeout>
```

### Mouse
```
CLICK `<selector>`
CLICK <x> <y>
DOUBLE_CLICK `<selector>`
RIGHT_CLICK `<selector>`
SCROLL <UP|DOWN|LEFT|RIGHT> <pixels>
MOVE <x> <y>
DRAG <x1> <y1> <x2> <y2>
```

### Keyboard
```
TYPE "<text>"
TYPE $<variable>
PRESS <key>
KEY_DOWN <Shift|Control|Alt|Meta>
KEY_UP <key>
CLEAR `<selector>`
SET `<selector>` "<value>"
```

### Control Flow
```
IF (EXISTS `<selector>`) THEN <command>
IF (EXISTS `<selector>`) THEN <command> ELSE <command>
IF (NOT EXISTS `<selector>`) THEN <command>
IF (`<javascript>`) THEN <command>
REPEAT (<command>, <count>)
REPEAT (<command>, `<condition>`)
```

### Variables & JS
```
SETVAR <name> = "<value>"
EVAL `<javascript>`
```

### Procedures
```
PROC <name>
  <commands>
ENDPROC

<procedure_name>
```

### Comments
```
# <comment>
```

## Usage in Crawl4AI

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

script = """
WAIT `#content` 5
CLICK `.load-more-button`
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-all`
"""

config = CrawlerRunConfig(
    c4a_script=script,
    wait_for=".content",
    screenshot=True
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
```