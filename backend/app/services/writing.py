import re
from typing import List, Dict, Tuple, Optional
from pi_agent.tools.base import Tool

WRITING_SKILL_PROMPT = """
WRITING SKILL INSTRUCTIONS:
When the user explicitly asks you to write an essay, article, long-form post, guide, checklist, or generate an HTML/Markdown document, you MUST invoke your dedicated Writing Skill.
When invoking this skill, you must wrap your final generated document inside an XML artifact block formatted as:

<artifact type="markdown" title="Your Document Title">
... your document content here ...
</artifact>

Or for HTML pages:
<artifact type="html" title="Your Page Title">
... HTML content here ...
</artifact>

ESSAY GUIDELINES (Ship 30 for 30 style):
If asked to write an essay:
- Target length is approximately 1,250 words.
- Use a compelling headline and a strong opening hook that captures immediate interest.
- Focus on one central, high-leverage idea with structured, logical progression.
- Structure for skimmability: use clear section headers (##), bold key concepts, and concise bullet points.
- Provide concrete, grounded examples and actionable takeaways.
- Include a memorable, resonant conclusion.
- Ground your claims in retrieved evidence from Lenny's Podcast transcripts where applicable.
- Clearly distinguish sourced claims from general reasoning.
- Never invent podcast quotations, episode numbers, links, or timestamps.

CONVERSATIONAL COMPANION:
Provide a brief, helpful conversational introduction outside the artifact block explaining what you have created.
Do NOT output the `<artifact>` block for simple questions or short conversational chat responses; only use it when a substantial document, essay, guide, or page is requested.
"""

def create_artifact_handler(args: dict, sandbox) -> str:
    """Tool handler for Pi Agent to generate artifacts."""
    title = args.get("title", "Generated Document").strip()
    artifact_type = args.get("artifact_type", "markdown").strip().lower()
    if artifact_type not in ["markdown", "html", "text"]:
        artifact_type = "markdown"
    content = args.get("content", "").strip()
    return f'<artifact type="{artifact_type}" title="{title}">\n{content}\n</artifact>'

writing_tool = Tool(
    name="create_artifact",
    description="Dedicated Writing Skill: Generate and format a structured document, essay, guide, checklist, or HTML page as an artifact.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "The headline or title of the document"},
            "artifact_type": {"type": "string", "enum": ["markdown", "html", "text"], "description": "The artifact type"},
            "content": {"type": "string", "description": "The complete markdown or html content of the document"}
        },
        "required": ["title", "artifact_type", "content"]
    },
    handler=create_artifact_handler,
    mutating=False
)


def _parse_attributes(tag_str: str) -> Dict[str, str]:
    """Robustly extracts key-value attributes from an XML/HTML opening tag."""
    attrs = {}
    attr_pattern = re.compile(r'([a-zA-Z_:][a-zA-Z0-9_\.:-]*)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))')
    for match in attr_pattern.finditer(tag_str):
        key = match.group(1).lower()
        val = match.group(2) if match.group(2) is not None else (
            match.group(3) if match.group(3) is not None else match.group(4)
        )
        attrs[key] = val.strip() if val else ""
    return attrs


def extract_artifacts(response_text: str, user_request: Optional[str] = None) -> Tuple[str, List[Dict[str, str]]]:
    """
    Parses the response text to find <artifact> blocks reliably.
    Handles:
    - Any attribute ordering (e.g. title first or type first).
    - Unquoted, single-quoted, and double-quoted attribute values.
    - Multiline markdown, code blocks, tables, and HTML.
    - Malformed or unclosed <artifact> blocks without losing content.
    - Missing <artifact> blocks when a document was requested and returned as structured markdown.
    - Preserves normal conversational responses.
    
    Returns:
        (cleaned_response_text, list_of_artifacts)
    """
    if not response_text:
        return "", []

    artifacts: List[Dict[str, str]] = []
    
    # 1. Look for standard or variant <artifact ...> tags
    open_tag_pattern = re.compile(r'<artifact\b([^>]*)>', re.IGNORECASE)
    close_tag_pattern = re.compile(r'</\s*artifact\s*>', re.IGNORECASE)

    segments = []
    last_idx = 0

    open_matches = list(open_tag_pattern.finditer(response_text))
    
    if open_matches:
        for i, open_match in enumerate(open_matches):
            start_open = open_match.start()
            end_open = open_match.end()
            
            # Text before this artifact
            if start_open > last_idx:
                segments.append(response_text[last_idx:start_open])
            
            attr_str = open_match.group(1)
            attrs = _parse_attributes(attr_str)
            
            artifact_type = attrs.get("type", "").lower() or "markdown"
            if artifact_type not in ["markdown", "html", "text"]:
                artifact_type = "markdown"
                
            title = attrs.get("title", "").strip()

            # Find matching close tag after end_open
            close_match = close_tag_pattern.search(response_text, end_open)
            
            # Check if there is another open tag before this close tag (in case of unclosed tags)
            next_open = open_matches[i + 1].start() if i + 1 < len(open_matches) else len(response_text)
            
            if close_match and close_match.start() < next_open:
                content = response_text[end_open:close_match.start()].strip()
                last_idx = close_match.end()
            else:
                # Unclosed artifact tag: take content until next artifact tag or end of text
                content = response_text[end_open:next_open].strip()
                last_idx = next_open

            # If title was not in attributes, infer from first heading
            if not title:
                heading_match = re.search(r'^#+\s*(.+)$', content, re.MULTILINE)
                if heading_match:
                    title = heading_match.group(1).strip()
                else:
                    title = "Generated Document"

            artifacts.append({
                "type": artifact_type,
                "title": title,
                "content": content
            })
            
            segments.append(f"\n*[Generated Artifact: {title}]*\n")

        if last_idx < len(response_text):
            segments.append(response_text[last_idx:])
            
        cleaned_text = "".join(segments).strip()
        
        # If the cleaned text is only placeholder or empty, provide a clean intro
        if not cleaned_text or cleaned_text.startswith("*[Generated Artifact:"):
            first_title = artifacts[0]["title"] if artifacts else "Document"
            cleaned_text = f"I've generated the requested document for you:\n\n*[Generated Artifact: {first_title}]*"

        return cleaned_text, artifacts

    # 2. Check for malformed opening tag e.g. `<artifact ...` without `>`
    malformed_open = re.search(r'<artifact\b([^>\n]*)', response_text, re.IGNORECASE)
    if malformed_open:
        start_idx = malformed_open.start()
        before_text = response_text[:start_idx].strip()
        attr_part = malformed_open.group(1)
        attrs = _parse_attributes(attr_part)
        
        artifact_type = attrs.get("type", "").lower() or "markdown"
        title = attrs.get("title", "").strip() or "Generated Document"
        
        # Content is after the opening pattern
        after_open = response_text[malformed_open.end():].lstrip(">").strip()
        # Remove any stray closing tag
        content = re.sub(r'</\s*artifact\s*>', '', after_open, flags=re.IGNORECASE).strip()
        
        if content:
            if title == "Generated Document":
                heading_match = re.search(r'^#+\s*(.+)$', content, re.MULTILINE)
                if heading_match:
                    title = heading_match.group(1).strip()

            artifacts.append({
                "type": artifact_type if artifact_type in ["markdown", "html", "text"] else "markdown",
                "title": title,
                "content": content
            })
            cleaned_text = f"{before_text}\n\n*[Generated Artifact: {title}]*".strip()
            return cleaned_text, artifacts

    # 3. Fallback: If user request or content clearly indicates a full essay/document was requested
    # and the model returned an essay (e.g. structured with markdown headings and substantial length)
    is_essay_request = False
    if user_request:
        req_lower = user_request.lower()
        is_essay_request = any(kw in req_lower for kw in ["essay", "write an essay", "article", "draft a", "create a document", "1,250", "1250"])

    lines = response_text.strip().splitlines()
    has_top_heading = any(line.strip().startswith("# ") for line in lines[:10])
    word_count = len(response_text.split())

    if (is_essay_request and (has_top_heading or word_count >= 50)) or (has_top_heading and word_count >= 150):
        # Extract title from the first `# ` heading
        title = "Generated Essay"
        doc_start_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("# "):
                title = line.strip().lstrip("#").strip()
                doc_start_idx = i
                break
        
        convo_intro = "\n".join(lines[:doc_start_idx]).strip()
        doc_content = "\n".join(lines[doc_start_idx:]).strip()
        if not doc_content:
            doc_content = response_text.strip()
            convo_intro = ""

        artifacts.append({
            "type": "markdown",
            "title": title,
            "content": doc_content
        })
        
        cleaned_text = f"{convo_intro}\n\n*[Generated Artifact: {title}]*".strip()
        if not convo_intro:
            cleaned_text = f"I've generated the requested document for you:\n\n*[Generated Artifact: {title}]*"
            
        return cleaned_text, artifacts

    # Normal conversational response without artifacts
    return response_text.strip(), []
