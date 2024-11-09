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


        /* 모달 스타일 */
        #modal {
            display: block; /* 기본적으로 표시 */
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border: 1px solid black;
            padding: 20px;
            z-index: 1000;
            width: 80%;
            max-width: 600px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
        }
        #overlay {
                display: block;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999;
        }
        
        /* 닫기 버튼 스타일 */
        #modal button {
                position: absolute;
                top: 5px;
                right: 5px;
                border: none;
                background: none;
                font-size: 20px;
                cursor: pointer;
        }
        
        .expander {
        max-width: 800px;  /* 원하는 최대 너비로 설정 */
        width: 100%;        /* 가로 전체로 확장 */
        }


        </style>
        """, unsafe_allow_html=True
    )
