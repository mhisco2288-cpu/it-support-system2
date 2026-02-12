import streamlit as st
import pandas as pd
import sqlite3
import requests
import time
import asyncio
import threading
import nest_asyncio
import plotly.express as px
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
from streamlit_option_menu import option_menu

# --- 1. إعدادات النظام ---
nest_asyncio.apply()
st.set_page_config(page_title="TechAssist Pro", page_icon="🚀", layout="wide")

# 🔴🔴🔴 ضع التوكين الخاص بك هنا 🔴🔴🔴
TOKEN = "7690158561:AAH9kiOjUNZIErzlWUtYdAzOThRGRLoBkLc"

# ==========================================
# 🎨 محرك التصميم (CSS Design Engine)
# ==========================================
st.markdown("""
<style>
    /* استيراد الخط العربي */
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;500;700;900&display=swap');
    
    /* تطبيق الخط على كل شيء */
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif;
    }

    /* الخلفية المتدرجة الاحترافية (Dark Blue Gradient) */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
    }

    /* تصميم القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.4);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* البطاقات الزجاجية (Glassmorphism Cards) */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        padding: 20px;
        transition: transform 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border-color: #00d2ff;
    }

    /* تلوين الأرقام */
    div[data-testid="stMetricValue"] {
        color: #00d2ff !important;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.5);
    }

    /* تصميم الجداول */
    div[data-testid="stDataFrame"] {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 15px;
        padding: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* الأزرار */
    .stButton > button {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton > button:hover {
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.7);
    }
    
    /* جعل النصوص من اليمين لليسار */
    .block-container {
        direction: rtl;
    }
    
    /* تخصيص العناوين */
    h1, h2, h3 {
        color: white !important;
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('tech_assist.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS support_tickets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ticket_ref TEXT,
                  user_id INTEGER,
                  username TEXT,
                  category TEXT,
                  details TEXT,
                  location TEXT,
                  phone TEXT,
                  status TEXT DEFAULT 'جديد',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. البوت (نفس المنطق السابق) ---
CAT, DETAIL, LOC, PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **مرحباً بك في TechAssist**\n\nنظام الدعم الفني الذكي.\nلفتح تذكرة، اختر القسم:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💻 حاسب آلي", callback_data='Computer'), InlineKeyboardButton("🌐 شبكات", callback_data='Network')],
            [InlineKeyboardButton("🖨️ طابعات", callback_data='Printer'), InlineKeyboardButton("🔑 أخرى", callback_data='Other')]
        ])
    )
    return CAT

async def get_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['cat'] = query.data
    await query.edit_message_text(f"القسم: {query.data}\n📝 صف المشكلة بالتفصيل:")
    return DETAIL

async def get_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['detail'] = update.message.text
    await update.message.reply_text("📍 الموقع (المكتب/الغرفة):")
    return LOC

async def get_loc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['loc'] = update.message.text
    await update.message.reply_text("📞 رقم جوال للتواصل:")
    return PHONE

async def save_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    user = update.message.from_user
    data = context.user_data
    ref = f"TIC-{int(time.time())}"
    
    conn = sqlite3.connect('tech_assist.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO support_tickets (ticket_ref, user_id, username, category, details, location, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (ref, user.id, user.first_name, data['cat'], data['detail'], data['loc'], phone))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ تم رفع الطلب بنجاح!\nرقم التذكرة: `{ref}`")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END

def run_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CAT: [CallbackQueryHandler(get_cat)],
            DETAIL: [MessageHandler(filters.TEXT, get_detail)],
            LOC: [MessageHandler(filters.TEXT, get_loc)],
            PHONE: [MessageHandler(filters.TEXT, save_data)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(conv)
    try: loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
    except: pass
    app.run_polling()

if not any(t.name == "TechAssistBot" for t in threading.enumerate()):
    t = threading.Thread(target=run_bot_thread, name="TechAssistBot", daemon=True)
    t.start()

# --- 4. واجهة الموقع الجديدة 🖥️ ---
with st.sidebar:
    st.markdown("### ⚙️ لوحة التحكم")
    page = option_menu("القائمة", ["لوحة القيادة", "التذاكر", "الأرشيف"], 
                       icons=['speedometer2', 'ticket-detailed', 'archive'],
                       menu_icon="cast", default_index=0,
                       styles={
                           "container": {"padding": "5!important", "background-color": "transparent"},
                           "icon": {"color": "#00d2ff", "font-size": "20px"}, 
                           "nav-link": {"font-size": "16px", "text-align": "right", "margin":"0px", "--hover-color": "#eee"},
                           "nav-link-selected": {"background-color": "#00d2ff"},
                       })

def get_tickets():
    conn = sqlite3.connect('tech_assist.db')
    df = pd.read_sql_query("SELECT * FROM support_tickets ORDER BY id DESC", conn)
    conn.close()
    return df

if page == "لوحة القيادة":
    st.title("🚀 مركز العمليات")
    st.markdown("---")
    
    df = get_tickets()
    if not df.empty:
        # البطاقات العلوية
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 الكل", len(df))
        col2.metric("🆕 جديد", len(df[df['status']=='جديد']))
        col3.metric("🔄 قيد العمل", len(df[df['status']=='قيد العمل']))
        col4.metric("✅ مكتمل", len(df[df['status']=='مكتمل']))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # الرسوم البيانية
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 التوزيع حسب الأقسام")
            fig = px.pie(df, names='category', hole=0.5, color_discrete_sequence=px.colors.qualitative.Cyan)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.subheader("📈 حالة التذاكر")
            fig2 = px.bar(df, x='status', color='category', barmode='group')
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig2, use_container_width=True)

elif page == "التذاكر":
    st.title("🎫 التذاكر النشطة")
    st.markdown("---")
    if st.button("🔄 تحديث البيانات"): st.rerun()
    
    df = get_tickets()
    active = df[df['status'] != 'مكتمل']
    
    if active.empty:
        st.success("🎉 ممتاز! لا توجد تذاكر نشطة حالياً.")
    else:
        for i, row in active.iterrows():
            # تصميم مخصص لكل تذكرة
            with st.expander(f"📌 {row['category']} | {row['username']} (Ref: {row['ticket_ref']})"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**📝 الوصف:** {row['details']}")
                    st.markdown(f"**📍 الموقع:** {row['location']}")
                    st.markdown(f"**📞 الهاتف:** {row['phone']}")
                    st.caption(f"تاريخ الطلب: {row['created_at']}")
                
                with c2:
                    st.markdown("#### الإجراء:")
                    new_status = st.selectbox("تغيير الحالة", ["جديد", "قيد العمل", "مكتمل"], key=f"s_{row['id']}", index=["جديد", "قيد العمل", "مكتمل"].index(row['status']))
                    if st.button("حفظ التغيير", key=f"b_{row['id']}"):
                        conn = sqlite3.connect('tech_assist.db')
                        conn.execute("UPDATE support_tickets SET status=? WHERE id=?", (new_status, row['id']))
                        conn.commit()
                        conn.close()
                        st.success("تم التحديث!")
                        time.sleep(0.5)
                        st.rerun()

elif page == "الأرشيف":
    st.title("🗄️ الأرشيف")
    st.markdown("---")
    df = get_tickets()
    st.dataframe(df, use_container_width=True)
