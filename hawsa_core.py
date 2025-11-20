import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

# ==========================
# 1) نظام الذاكرة المتقدمة
# ==========================

class HawsaAdvancedMemory:
    """
    ذاكرة متقدمة تحفظ:
    - سجل المحادثات
    - ملاحظات تقنية
    - قرارات سابقة
    وتسمح باسترجاع سياق ذكي لكل مستخدم.
    """
    def __init__(self, db_path: str = "hawsa_ai_memory.db"):
        self.db_path = db_path
        self._init_memory_tables()
    
    def _init_memory_tables(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # سجل المحادثات
        c.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,                -- 'user' أو 'assistant'
                content TEXT,
                summary TEXT,
                tags TEXT,                -- JSON list
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ملاحظات طويلة المدى (معرفة المستخدم / تفضيلاته)
        c.execute("""
            CREATE TABLE IF NOT EXISTS long_term_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                note_type TEXT,           -- 'preference', 'project', 'skill'
                note_text TEXT,
                importance REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_interaction(
        self,
        user_id: str,
        role: str,
        content: str,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None
    ):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO conversation_memory (user_id, role, content, summary, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, role, content, summary or "", json.dumps(tags or [], ensure_ascii=False)))
        conn.commit()
        conn.close()
    
    def get_recent_context(self, user_id: str, limit: int = 8) -> List[Dict[str, Any]]:
        """إرجاع آخر N رسائل كمصدر سياق للذكاء."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT role, content, created_at, tags
            FROM conversation_memory
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = c.fetchall()
        conn.close()
        
        context = []
        for role, content, created_at, tags in rows[::-1]:
            try:
                tags_list = json.loads(tags) if tags else []
            except Exception:
                tags_list = []
            context.append({
                "role": role,
                "content": content,
                "created_at": created_at,
                "tags": tags_list
            })
        return context
    
    def add_long_term_note(
        self,
        user_id: str,
        note_text: str,
        note_type: str = "preference",
        importance: float = 1.0
    ):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO long_term_notes (user_id, note_type, note_text, importance)
            VALUES (?, ?, ?, ?)
        """, (user_id, note_type, note_text, importance))
        conn.commit()
        conn.close()
    
    def get_long_term_notes(
        self,
        user_id: str,
        note_type: Optional[str] = None
    ) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if note_type:
            c.execute("""
                SELECT note_text FROM long_term_notes
                WHERE user_id = ? AND note_type = ?
                ORDER BY importance DESC, id DESC
            """, (user_id, note_type))
        else:
            c.execute("""
                SELECT note_text FROM long_term_notes
                WHERE user_id = ?
                ORDER BY importance DESC, id DESC
            """, (user_id,))
        
        notes = [row[0] for row in c.fetchall()]
        conn.close()
        return notes

# ==========================
# 2) أنواع وتحليل المستخدم
# ==========================

class PersonalityType(Enum):
    ANALYTICAL = "ANALYTICAL"
    CREATIVE = "CREATIVE"
    PRACTICAL = "PRACTICAL"

class ExpertiseLevel(Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"

class ContentType(Enum):
    TEXT = "TEXT"
    BULLETS = "BULLETS"
    CODE = "CODE"

class UserProfile:
    def __init__(
        self,
        user_id: str,
        personality_type: PersonalityType = PersonalityType.ANALYTICAL,
        expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE,
        technical_interests: Optional[List[str]] = None,
        confidence_score: float = 0.5,
        preferred_content_types: Optional[List[ContentType]] = None
    ):
        self.user_id = user_id
        self.personality_type = personality_type
        self.expertise_level = expertise_level
        self.technical_interests = technical_interests or []
        self.confidence_score = confidence_score
        self.preferred_content_types = preferred_content_types or [ContentType.TEXT]

class AdvancedUserAnalytics:
    """
    يحلل رسالة المستخدم ويستنتج:
    - نوع الشخصية
    - مستوى الخبرة
    - الاهتمامات التقنية
    ويحفظ بروفايل في قاعدة بيانات منفصلة.
    """
    def __init__(self, db_path: str = "hawsa_ai_advanced.db", memory: HawsaAdvancedMemory = None):
        self.db_path = db_path
        self.memory = memory  # لربط التحليل بالذاكرة الطويلة
        self._init_analytics_tables()
    
    def _init_analytics_tables(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                personality TEXT,
                expertise TEXT,
                interests TEXT,
                confidence REAL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def analyze_user_message(self, user_id: str, message: str, base_confidence: float = 0.0) -> UserProfile:
        msg_lower = message.lower()
        
        # تحليل بسيط مبدئي حسب الكلمات
        if any(k in msg_lower for k in ["كود", "code", "script", "برمجة"]):
            personality = PersonalityType.ANALYTICAL
            expertise = ExpertiseLevel.ADVANCED
            interests = ["programming", "systems", "automation"]
        elif any(k in msg_lower for k in ["تصميم", "ui", "ux", "واجهة"]):
            personality = PersonalityType.CREATIVE
            expertise = ExpertiseLevel.INTERMEDIATE
            interests = ["design", "ui/ux"]
        else:
            personality = PersonalityType.PRACTICAL
            expertise = ExpertiseLevel.INTERMEDIATE
            interests = ["general_engineering"]
        
        confidence = min(1.0, 0.4 + base_confidence + len(message) / 200.0)
        
        preferred = [ContentType.TEXT]
        if len(message) > 60:
            preferred.append(ContentType.BULLETS)
        
        profile = UserProfile(
            user_id=user_id,
            personality_type=personality,
            expertise_level=expertise,
            technical_interests=interests,
            confidence_score=confidence,
            preferred_content_types=preferred
        )
        
        # حفظ البروفايل في قاعدة البيانات
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO user_profiles (user_id, personality, expertise, interests, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                personality=excluded.personality,
                expertise=excluded.expertise,
                interests=excluded.interests,
                confidence=excluded.confidence,
                updated_at=CURRENT_TIMESTAMP
        """, (
            user_id,
            profile.personality_type.value,
            profile.expertise_level.value,
            json.dumps(interests, ensure_ascii=False),
            confidence
        ))
        conn.commit()
        conn.close()
        
        # حفظ ملاحظة طويلة المدى عن اهتمامات المستخدم
        try:
            if self.memory and interests:
                self.memory.add_long_term_note(
                    user_id=user_id,
                    note_text=f"اهتمامات تقنية: {', '.join(interests)}",
                    note_type="tech_interests",
                    importance=1.5
                )
        except Exception:
            pass
        
        return profile

# ==========================
# 3) بيانات هندسية + ميديا
# ==========================

class EngineeringDataIntegration:
    """نواة بسيطة لتوصيات ECU / تشخيص."""
    def __init__(self):
        pass
    
    def get_ecu_recommendations(self, vehicle_id: str, description: str) -> List[Dict[str, Any]]:
        recs = []
        desc_low = description.lower()
        
        if "boost" in desc_low or "توربو" in desc_low:
            recs.append({
                "code": "BOOST_MAP_TUNE",
                "description": "ضبط خرائط البوست مع مراعاة حدود الأمان للـ AFR والحرارة."
            })
        if "dtc" in desc_low or "رمز" in desc_low:
            recs.append({
                "code": "DTC_ANALYSIS",
                "description": "تحليل رموز الأعطال وربطها بحالات فعلية من سجلات سابقة."
            })
        
        return recs

class MediaGenerator:
    """مولّد وسائط بسيط (ممكن تربطه لاحقًا بـ DALL·E أو غيره)."""
    def __init__(self):
        pass
    
    def generate_media(self, message: str, profile: UserProfile) -> Dict[str, Any]:
        if any(k in message.lower() for k in ["رسم", "diagram", "مخطط"]):
            return {
                "type": "diagram_description",
                "content": "مخطط نصي يشرح العلاقة بين وحدات النظام المقترح."
            }
        
        return {
            "type": "none",
            "content": ""
        }

# ==========================
# 4) مهام / Skills
# ==========================

class BaseSkill:
    """واجهة عامة لأي مهارة داخل Hawsa AI."""
    def can_handle(self, message: str) -> bool:
        raise NotImplementedError
    
    def handle(self, message: str, master: "HawsaCore") -> str:
        raise NotImplementedError

class EngineeringSkill(BaseSkill):
    """مهارة للمواضيع الهندسية / ECU / تشخيص / أنظمة."""
    KEYWORDS = ['ecu', 'برمجة', 'تشخيص', 'dtc', 'كود', 'رمز', 'خريطة', 'boost', 'توربو', 'خرائط']
    
    def can_handle(self, message: str) -> bool:
        low = message.lower()
        return any(k in low for k in self.KEYWORDS)
    
    def handle(self, message: str, master: "HawsaCore") -> str:
        recs = master.engineering_data.get_ecu_recommendations("UNKNOWN", message)
        lines = ["🛠 *معالجة هندسية متقدمة للطلب:*", f"- الوصف: {message}", ""]
        if recs:
            lines.append("*توصيات Hawsa AI:*")
            for r in recs:
                lines.append(f"• {r['description']}")
        else:
            lines.append("لم يتم العثور على توصيات محددة، سيتم تحليل الطلب نظريًا.")
        return "\n".join(lines)

class CreativeDesignSkill(BaseSkill):
    """مهارة للأفكار الإبداعية (تصميم، منصات، أفكار جديدة)."""
    KEYWORDS = ['فكرة', 'تصميم', 'منصة', 'واجهة', 'system', 'platform', 'ui', 'ux']
    
    def can_handle(self, message: str) -> bool:
        low = message.lower()
        return any(k in low for k in self.KEYWORDS)
    
    def handle(self, message: str, master: "HawsaCore") -> str:
        return (
            "🎨 *تحليل وتصميم إبداعي للطلب:*\n"
            f"النص المدخل: {message}\n\n"
            "- تقسيم الفكرة لوحدات (Modules)\n"
            "- اقتراح بنية System Architecture\n"
            "- تحديد نقاط التكامل مع Hawsa AI Core\n"
        )

# ==========================
# 5) HawsaCore - العقل الموحد
# ==========================

class HawsaCore:
    """
    هذا هو اللب / النواة:
    - يتعامل مع الذاكرة
    - يحلل المستخدم
    - يختار Skill
    - يولد رد مخصص
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.memory = HawsaAdvancedMemory()
        self.user_analytics = AdvancedUserAnalytics(memory=self.memory)
        self.engineering_data = EngineeringDataIntegration()
        self.media_generator = MediaGenerator()
        
        self.current_user_profile: Optional[UserProfile] = None
        
        # تسجيل المهارات
        self.skills: List[BaseSkill] = [
            EngineeringSkill(),
            CreativeDesignSkill(),
            # لاحقًا تضيف Skills جديدة هنا
        ]
    
    def _generate_base_response(self, message: str) -> str:
        return (
            "🔍 تحليل أولي لرسالتك:\n"
            f"- المحتوى: {message}\n"
            "- سيتم الآن دمج خبرة Hawsa AI مع أسلوبك الشخصي في البرمجة والتحليل.\n"
        )
    
    def _personalize_response(self, base_response: str, profile: UserProfile) -> str:
        intro = ""
        if profile.personality_type == PersonalityType.ANALYTICAL:
            intro = "أشوف إن أسلوبك تحليلي وموجه للمنطق 👨‍💻، فبحاول أكون مباشر ومنظم.\n"
        elif profile.personality_type == PersonalityType.CREATIVE:
            intro = "أسلوبك فيه لمسة إبداع 🎨، فبحاول أفتح لك أفكار وتفرعات.\n"
        else:
            intro = "واضح إنك تحب النتائج العملية 👊، فبنركز على خطوات واضحة وسريعة.\n"
        
        return intro + "\n" + base_response
    
    def _generate_media_content(self, message: str, profile: UserProfile) -> Dict[str, Any]:
        return self.media_generator.generate_media(message, profile)
    
    def _get_personalized_notes(self) -> List[str]:
        # ممكن لاحقًا تسترجع ملاحظات من الذاكرة حسب user_id
        return []
    
    def _route_to_skill(self, message: str) -> Optional[str]:
        """اختيار المهارة الأنسب للرسالة (لو فيه مهارة مناسبة)."""
        for skill in self.skills:
            try:
                if skill.can_handle(message):
                    return skill.handle(message, self)
            except Exception as e:
                print(f"[Skill Error] {skill.__class__.__name__}: {e}")
        return None
    
    def process_comprehensive_query(self, user_id: str, user_message: str) -> Dict[str, Any]:
        """الدالة الرئيسية لمعالجة أي رسالة."""
        start_time = datetime.now()
        
        # 0. قراءة سياق سابق لنفس المستخدم
        recent_context = self.memory.get_recent_context(user_id, limit=6)
        
        # 1. تحليل المستخدم
        self.current_user_profile = self.user_analytics.analyze_user_message(
            user_id, user_message, 0.0
        )
        
        # 2. البحث في المعرفة الهندسية
        technical_recommendations = self.engineering_data.get_ecu_recommendations(
            "UNKNOWN", user_message
        )
        
        # 3. توليد الرد الأساسي
        base_response = self._generate_base_response(user_message)
        
        # 3.1 معالجة متقدمة عبر المهارات
        skill_response = self._route_to_skill(user_message)
        if skill_response:
            base_response = base_response + "\n\n" + skill_response
        
        # 4. تخصيص الرد حسب شخصية المستخدم وخبرته
        personalized_response = self._personalize_response(
            base_response, self.current_user_profile
        )
        
        # 5. إنشاء الوسائط المناسبة
        media_content = self._generate_media_content(user_message, self.current_user_profile)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 6. حفظ التفاعل في الذاكرة (user + assistant)
        try:
            self.memory.save_interaction(
                user_id=user_id,
                role="user",
                content=user_message,
                tags=["input"]
            )
            self.memory.save_interaction(
                user_id=user_id,
                role="assistant",
                content=personalized_response,
                tags=["response"]
            )
        except Exception as e:
            print(f"[Memory Error] {e}")
        
        return {
            'success': True,
            'user_id': user_id,
            'user_profile': {
                'personality': self.current_user_profile.personality_type.value,
                'expertise': self.current_user_profile.expertise_level.value,
                'interests': self.current_user_profile.technical_interests,
                'confidence': self.current_user_profile.confidence_score
            },
            'context_used': recent_context,
            'response': {
                'text': personalized_response,
                'technical_recommendations': technical_recommendations,
                'personalized_notes': self._get_personalized_notes()
            },
            'media': media_content,
            'analytics': {
                'processing_time_seconds': processing_time,
                'content_types_generated': [ct.value for ct in self.current_user_profile.preferred_content_types],
                'interaction_quality': 'HIGH' if len(user_message) > 20 else 'MEDIUM'
            }
        }

# ==========================
# 6) وضع التشغيل التجريبي (CLI)
# ==========================

if __name__ == "__main__":
    core = HawsaCore()
    user_id = "mohammed_hawsa"  # تقدر تغيره لمعرف ثابت لك
    
    print("🔥 Hawsa AI Core جاهز. اكتب رسالتك (أو اكتب exit للخروج).")
    
    while True:
        try:
            msg = input("\nأنت: ")
        except EOFError:
            break
        
        if msg.strip().lower() in ["exit", "quit", "خروج"]:
            print("Hawsa AI: يعطيك العافية 🤝")
            break
        
        result = core.process_comprehensive_query(user_id, msg)
        print("\nHawsa AI:\n", result["response"]["text"])
