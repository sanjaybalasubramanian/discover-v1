"""LLM integration module"""
from app.llm.client import parse_job_listing, extract_best_contacts, ParsedJob, ExtractedContact

__all__ = ['parse_job_listing', 'extract_best_contacts', 'ParsedJob', 'ExtractedContact']
