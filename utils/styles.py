import streamlit as st

def set_global_styles():
    """앱의 전역 스타일 설정"""
    st.markdown(
        """
        <style>
        .stTextInput, .stButton {
            height: 38px;
        }
        .video-title {
            font-size: 16px;
            font-weight: bold;
            height: 70px;
            white-space: normal;
            overflow-wrap: break-word;
            margin-bottom: 10px;
        }

        .video-title2 {
            font-size: 16px;
            font-weight: bold;
            height: 70px; /* 제목의 고정된 높이 */
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            display: block; /* 제목이 블록 요소로 처리되도록 설정 */
        }

        .thumbnail {
            width: 100%;
        }
        .comment-container {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        .icon {
            font-size: 20px;
            margin-right: 8px;
        }
        .comment-text {
            width: 100%;
            height: 60px;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }

        .expander {
        max-width: 800px;  /* 원하는 최대 너비로 설정 */
        width: 100%;        /* 가로 전체로 확장 */
        }

        .
        </style>
        """, unsafe_allow_html=True
    )
