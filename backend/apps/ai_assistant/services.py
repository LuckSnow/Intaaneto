import openai
from django.conf import settings
from typing import List, Dict
import time

openai.api_key = settings.OPENAI_API_KEY


class AIService:
    """AI Assistant Service using OpenAI"""
    
    SYSTEM_PROMPT = """
    Bạn là trợ lý AI dành cho học sinh cấp 2 học lập trình web.
    Nhiệm vụ của bạn:
    1. Giải thích kiến thức đơn giản, dễ hiểu
    2. Hướng dẫn làm bài tập (KHÔNG cho đáp án trực tiếp)
    3. Trả lời câu hỏi bằng tiếng Việt
    4. Sử dụng ví dụ thực tế, gần gũi với học sinh
    5. Khuyến khích tư duy độc lập
    
    Lưu ý:
    - Luôn động viên và tạo động lực cho học sinh
    - Tránh thuật ngữ khó, nếu dùng thì giải thích rõ
    - Chia nhỏ vấn đề phức tạp thành các bước đơn giản
    """
    
    @staticmethod
    def chat(messages: List[Dict[str, str]], context: Dict = None) -> Dict:
        """
        Send chat request to OpenAI
        
        Args:
            messages: List of chat messages
            context: Additional context (lesson, exercise, etc.)
        
        Returns:
            Response dict with content, tokens, and time
        """
        try:
            start_time = time.time()
            
            # Add system prompt
            full_messages = [
                {"role": "system", "content": AIService.SYSTEM_PROMPT}
            ]
            
            # Add context if provided
            if context:
                context_message = AIService._build_context_message(context)
                full_messages.append({"role": "system", "content": context_message})
            
            # Add user messages
            full_messages.extend(messages)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=full_messages,
                temperature=0.7,
                max_tokens=1000,
            )
            
            end_time = time.time()
            
            return {
                'content': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'response_time_ms': int((end_time - start_time) * 1000),
                'success': True
            }
            
        except Exception as e:
            return {
                'content': f'Xin lỗi, có lỗi xảy ra: {str(e)}',
                'tokens_used': 0,
                'response_time_ms': 0,
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _build_context_message(context: Dict) -> str:
        """Build context message from context dict"""
        context_parts = []
        
        if 'lesson' in context:
            context_parts.append(f"Bài học hiện tại: {context['lesson']}")
        
        if 'exercise' in context:
            context_parts.append(f"Bài tập: {context['exercise']}")
        
        if 'code' in context:
            code_section = f"Code của học sinh:\n```\n{context['code']}\n```"
            context_parts.append(code_section)
        
        return "\n".join(context_parts)
    
    @staticmethod
    def explain_code(code: str, language: str = 'javascript') -> str:
        """Explain code to students"""
        code_block = f"```{language}\n{code}\n```"
        prompt = f"""
        Giải thích đoạn code {language} sau cho học sinh cấp 2:
        
        {code_block}
        
        Hãy giải thích:
        1. Code này làm gì?
        2. Các khái niệm chính
        3. Cách hoạt động từng phần
        """
        
        response = AIService.chat([
            {"role": "user", "content": prompt}
        ])
        
        return response['content']
    
    @staticmethod
    def give_hint(exercise_description: str, student_code: str = '') -> str:
        """Give hint for exercise"""
        student_code_section = f"Code hiện tại của học sinh:\n```\n{student_code}\n```" if student_code else ""
        prompt = f"""
        Bài tập: {exercise_description}
        
        {student_code_section}
        
        Hãy cho gợi ý (KHÔNG cho đáp án):
        - Hướng tiếp cận
        - Các bước cần làm
        - Khái niệm cần sử dụng
        """
        
        response = AIService.chat([
            {"role": "user", "content": prompt}
        ])
        
        return response['content']
