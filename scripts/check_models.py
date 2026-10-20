#!/usr/bin/env python
"""Check available Claude models on AWS Bedrock"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    'bedrock',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

try:
    response = client.list_foundation_models(byProvider='Anthropic')
    
    print("=" * 60)
    print("AVAILABLE ANTHROPIC CLAUDE MODELS ON AWS BEDROCK")
    print("=" * 60)
    print()
    
    claude_models = [m for m in response['modelSummaries'] if 'claude' in m['modelId'].lower()]
    
    for model in sorted(claude_models, key=lambda x: x['modelId']):
        print(f"  • {model['modelId']}")
    
    print()
    print("=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
