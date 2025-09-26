"""
Professional response formatter for AI assistant.
Removes markdown formatting and ensures professional business communication.
"""

import re
from typing import Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProfessionalResponseFormatter:
    """Format AI responses to be professional and clean."""
    
    @staticmethod
    def clean_response(response: str) -> str:
        """Clean response while preserving strategic professional formatting."""
        
        if not response:
            return ""
        
        # Keep strategic bold formatting for professional presentation
        cleaned = response
        
        # KEEP bold formatting for key information (**text** stays **text**)
        # Only remove excessive markdown formatting
        
        # Remove excessive markdown headers (### -> text, but allow **Bold Headers**)
        cleaned = re.sub(r'^#{3,6}\s*', '', cleaned, flags=re.MULTILINE)  # ### Header -> Header
        cleaned = re.sub(r'^#{1,2}\s*([^*])', r'**\1**', cleaned, flags=re.MULTILINE)  # # Header -> **Header**
        
        # Remove italic formatting but keep bold - more precise pattern
        cleaned = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', cleaned)      # *italic* -> italic (but not **bold**)
        cleaned = re.sub(r'(?<!_)_([^_\n]+)_(?!_)', r'\1', cleaned)        # _italic_ -> italic (but not __bold__)
        
        # Clean up any stray asterisks that aren't part of bold formatting
        cleaned = re.sub(r'(?<!\*)\*(?!\*)', '', cleaned)  # Remove single * not part of **bold**
        
        # Clean up bullet points - keep them but make professional
        cleaned = re.sub(r'^\s*[-\*\+]\s*', '• ', cleaned, flags=re.MULTILINE)
        
        # Remove code blocks but keep content or replace with note
        cleaned = re.sub(r'```[\s\S]*?```', '[Technical details available in dashboard]', cleaned)
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)  # `code` -> code
        
        # Remove excessive emojis (keep business appropriate ones)
        business_emojis = ['📦', '📋', '🔍', '⚖️', '🏷️', '📊', '✅', '❌', '🌱', '🏭', '🏢', '🤝']
        emoji_pattern = r'[^\w\s' + ''.join(re.escape(emoji) for emoji in business_emojis) + r']'
        # Don't remove all emojis, just excessive decorative ones
        
        # Clean up excessive whitespace while preserving structure
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Multiple newlines -> double newline
        # DON'T collapse all whitespace - preserve line breaks and structure
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # Only collapse horizontal whitespace (spaces/tabs)
        cleaned = cleaned.strip()
        
        return cleaned
    
    @staticmethod
    def format_professional_response(response: str, context: Dict[str, Any]) -> str:
        """Format response in professional business style."""
        
        # Clean markdown first
        cleaned = ProfessionalResponseFormatter.clean_response(response)
        
        if not cleaned:
            return "I apologize, but I wasn't able to generate a proper response. Please try rephrasing your question."
        
        # Get user context for personalization
        user_info = context.get('user_info', {})
        user_name = user_info.get('name', '').split()[0] if user_info.get('name') else ''
        company_name = user_info.get('company_name', 'your company')
        
        # Ensure professional tone
        professional_response = cleaned
        
        # Add context-aware introduction for substantial responses
        if len(cleaned) > 100 and user_name and user_name.lower() != 'user':
            # Only add greeting for longer responses to avoid repetition
            if not professional_response.lower().startswith('hello') and not professional_response.lower().startswith('hi'):
                professional_response = f"Hello {user_name}, here's the information for {company_name}:\n\n{cleaned}"
        
        # Ensure professional business language
        professional_response = ProfessionalResponseFormatter._ensure_professional_tone(professional_response)
        
        return professional_response
    
    @staticmethod
    def _ensure_professional_tone(response: str) -> str:
        """Ensure the response uses professional business language."""
        
        # Replace casual expressions with professional ones
        replacements = {
            r'\bawesome\b': 'excellent',
            r'\bgreat\b': 'good',
            r'\bnice\b': 'good',
            r'\bcool\b': 'beneficial',
            r'\bstuff\b': 'items',
            r'\bthings\b': 'items',
            r'\bthanks\b': 'thank you',
            r'\bokay\b': 'understood',
            r'\bok\b': 'understood',
            r'\byep\b': 'yes',
            r'\bnope\b': 'no',
            r'\bguys\b': 'team members',
        }
        
        professional = response
        for pattern, replacement in replacements.items():
            professional = re.sub(pattern, replacement, professional, flags=re.IGNORECASE)
        
        return professional
    
    @staticmethod
    def format_data_response(data: Dict[str, Any], title: str = "") -> str:
        """Format data into professional business presentation."""
        
        if not data:
            return "No data available at this time."
        
        response_parts = []
        
        if title:
            response_parts.append(f"{title}:")
        
        # Format inventory data
        if 'inventory' in data:
            inv = data['inventory']
            response_parts.append(f"\nInventory Summary:")
            response_parts.append(f"• Total batches: {inv.get('total_batches', 0)}")
            response_parts.append(f"• Available batches: {inv.get('available_batches', 0)}")
            response_parts.append(f"• Total quantity: {inv.get('total_quantity', 0):.1f} MT")
            if inv.get('avg_transparency', 0) > 0:
                response_parts.append(f"• Average transparency score: {inv.get('avg_transparency', 0):.1f}%")
        
        # Format purchase order data
        if 'purchase_orders' in data:
            po = data['purchase_orders']
            response_parts.append(f"\nPurchase Order Activity:")
            response_parts.append(f"• Orders as buyer: {po.get('as_buyer', 0)}")
            response_parts.append(f"• Orders as seller: {po.get('as_seller', 0)}")
            if po.get('pending_orders', 0) > 0:
                response_parts.append(f"• Pending orders requiring attention: {po.get('pending_orders', 0)}")
        
        # Format trading partners
        if 'trading_partners' in data and data['trading_partners']:
            partners = data['trading_partners'][:5]  # Limit to 5
            response_parts.append(f"\nKey Trading Partners: {', '.join(partners)}")
        
        return '\n'.join(response_parts) if response_parts else "Data is currently being updated."
    
    @staticmethod
    def format_error_response(error_type: str, context: Dict[str, Any]) -> str:
        """Format professional error responses."""
        
        user_info = context.get('user_info', {})
        user_name = user_info.get('name', '').split()[0] if user_info.get('name') else ''
        company_name = user_info.get('company_name', 'your company')
        
        error_responses = {
            'data_unavailable': f"I apologize, but I'm unable to access the current data for {company_name}. Please check your dashboard directly or try again in a moment.",
            'feature_disabled': f"This feature is currently not enabled for {company_name}. Please contact your administrator for access.",
            'permission_denied': f"You don't have permission to access this information. Please contact your manager or administrator.",
            'system_error': f"I'm experiencing technical difficulties. Please try again or contact support if the issue persists.",
            'invalid_request': f"I'm not sure how to help with that request. Please try asking about inventory, purchase orders, transparency, or compliance."
        }
        
        base_response = error_responses.get(error_type, error_responses['system_error'])
        
        if user_name and user_name.lower() != 'user':
            return f"Hello {user_name}, {base_response.lower()}"
        else:
            return base_response
    
    @staticmethod
    def format_metrics_response(metrics: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Format metrics and KPIs in professional business format."""
        
        if not metrics:
            return "Metrics data is currently being calculated."
        
        response_parts = []
        
        # Format key performance indicators
        if 'transparency_score' in metrics:
            score = metrics['transparency_score']
            response_parts.append(f"Transparency Performance: {score:.1f}%")
            
            if score >= 95:
                response_parts.append("• Performance level: Excellent")
            elif score >= 85:
                response_parts.append("• Performance level: Good")
            elif score >= 70:
                response_parts.append("• Performance level: Acceptable")
            else:
                response_parts.append("• Performance level: Requires improvement")
        
        # Format compliance metrics
        if 'compliance' in metrics:
            comp = metrics['compliance']
            response_parts.append(f"\nCompliance Status:")
            if 'eudr_compliant' in comp:
                response_parts.append(f"• EUDR compliance: {comp['eudr_compliant']}/{comp.get('total_batches', 0)} batches")
            if 'rspo_compliant' in comp:
                response_parts.append(f"• RSPO compliance: {comp['rspo_compliant']}/{comp.get('total_batches', 0)} batches")
        
        # Format processing efficiency
        if 'processing_efficiency' in metrics:
            eff = metrics['processing_efficiency']
            response_parts.append(f"\nProcessing Efficiency: {eff}%")
        
        return '\n'.join(response_parts) if response_parts else "Metrics are being calculated."
