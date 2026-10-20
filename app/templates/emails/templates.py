"""
Email templates for outreach
Template selection based on job experience requirement
"""

TEMPLATE_A_STANDARD = """Hi,

I'm a GenAI Engineer with 2 years of hands-on experience in LLM applications, prompt engineering, and AI agent development. I came across {company}'s work and am interested in opportunities there.

I specialize in:
- Building production LLM systems (RAG, function calling, agentic workflows)
- Prompt engineering and optimization
- Python, LangChain, FastAPI, LangGraph
- AWS Bedrock, Claude, OpenAI APIs

I'm looking for roles where I can contribute to impactful AI products and continue growing in this space. Would love to discuss opportunities at {company}.

My resume is attached. Looking forward to hearing from you.

Best regards,
[Your Name]
"""

TEMPLATE_B_MISMATCH = """Hi,

I noticed {company}'s GenAI Engineer opening mentions {experience_required}+ years of experience. While I have 2 years in the field, I've worked extensively on production-grade LLM systems and believe my hands-on skills align closely with what you need.

In my 2 years, I've:
- Built and deployed multiple LLM applications from scratch
- Designed agentic workflows with LangGraph and Claude
- Optimized prompt engineering for 40% cost reduction
- Worked with RAG systems, function calling, and embeddings

The GenAI field is relatively new, and I've spent these 2 years deeply focused on building real-world applications rather than tangential work. I'm confident I can deliver value from day one.

Would appreciate the opportunity to discuss how my experience maps to your needs.

Resume attached. Happy to chat.

Best regards,
[Your Name]
"""


def get_template(experience_required: int = None) -> tuple[str, str]:
    """
    Get email template based on experience requirement
    
    Args:
        experience_required: Years of experience required by job
    
    Returns:
        (subject, body_template)
    """
    if experience_required and experience_required >= 4:
        return (
            "GenAI Engineer - Strong 2-Year Track Record",
            TEMPLATE_B_MISMATCH
        )
    else:
        return (
            "GenAI Engineer - 2 Years Experience",
            TEMPLATE_A_STANDARD
        )
