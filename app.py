import streamlit as st
import pandas as pd
import os
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

st.set_page_config(page_title="DueMate+", layout="wide")

TASK_FILE = "data/my_tasks.csv"
EXTERNAL_FILE = "data/external_deadlines.csv"

st.title("📚 DueMate+")
st.subheader("대학생 과제 및 대외활동 통합 마감 관리 웹앱")


def set_korean_font():
    try:
        import koreanize_matplotlib
    except:
        font_candidates = ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"]
        available_fonts = [f.name for f in fm.fontManager.ttflist]

        for font in font_candidates:
            if font in available_fonts:
                plt.rcParams["font.family"] = font
                break

    plt.rcParams["axes.unicode_minus"] = False


set_korean_font()


def load_tasks():
    columns = [
        "task_name", "subject", "deadline", "importance", "status",
        "memo", "type", "created_date", "completed_date"
    ]

    if os.path.exists(TASK_FILE) and os.path.getsize(TASK_FILE) > 0:
        df = pd.read_csv(TASK_FILE)

        for col in columns:
            if col not in df.columns:
                if col == "type":
                    df[col] = "과제"
                elif col == "created_date":
                    df[col] = pd.Timestamp.today().strftime("%Y-%m-%d")
                else:
                    df[col] = ""

        df = df[columns]

        for col in ["task_name", "subject", "importance", "status", "memo", "type", "created_date", "completed_date"]:
            df[col] = df[col].fillna("").astype(str)

        return df

    return pd.DataFrame(columns=columns)


def save_tasks(df):
    df = df.copy()
    for col in ["task_name", "subject", "importance", "status", "memo", "type", "created_date", "completed_date"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    df.to_csv(TASK_FILE, index=False, encoding="utf-8-sig")


def add_d_day(df, deadline_col="deadline"):
    df = df.copy()
    df[deadline_col] = pd.to_datetime(df[deadline_col], errors="coerce")
    today = pd.Timestamp.today().normalize()
    df["d_day"] = (df[deadline_col] - today).dt.days
    return df


def draw_pie_chart(series, title):
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(series.values, labels=series.index, autopct="%1.1f%%", startangle=90)
    ax.set_title(title, fontsize=15, pad=15)
    ax.axis("equal")
    st.pyplot(fig)


def draw_histogram(data, title, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(data.dropna(), bins=8, edgecolor="black")
    ax.set_title(title, fontsize=15, pad=15)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    st.pyplot(fig)


def draw_timeline(df):
    fig, ax = plt.subplots(figsize=(12, 5))

    df = df.copy()
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")
    df = df.dropna(subset=["deadline"])

    today = pd.Timestamp.today().normalize()
    end_day = today + pd.Timedelta(days=60)

    df = df[
        (df["deadline"] >= today) &
        (df["deadline"] <= end_day)
    ].sort_values("deadline")

    if len(df) == 0:
        st.info("앞으로 2개월 안에 마감되는 과제가 없습니다.")
        return

    ax.scatter(df["deadline"], range(len(df)), s=90)

    for i, row in enumerate(df.itertuples()):
        ax.text(row.deadline, i, f" {row.task_name}", va="center", fontsize=9)

    ax.set_xlim(today, end_day)
    ax.set_title("앞으로 2개월 내 과제 마감일 타임라인", fontsize=15, pad=15)
    ax.set_xlabel("마감일")
    ax.set_yticks([])
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    date_ticks = pd.date_range(today, end_day, freq="7D")
    ax.set_xticks(date_ticks)
    ax.set_xticklabels([d.strftime("%m-%d") for d in date_ticks], rotation=45)

    plt.tight_layout()
    st.pyplot(fig)


tasks = load_tasks()
external = pd.read_csv(EXTERNAL_FILE)
external = add_d_day(external)

menu = st.sidebar.radio(
    "메뉴",
    ["홈", "과제 등록", "과제 목록", "외부 일정 탐색", "추천", "통계", "데이터 설명"]
)


if menu == "홈":
    st.write("DueMate+는 대학생의 과제와 공모전/대외활동 마감일을 함께 관리하는 웹앱입니다.")

    tasks = add_d_day(tasks) if len(tasks) > 0 else tasks

    st.caption("마감 임박 기준: 내 일정은 D-3 이내, 외부 일정은 D-7 이내로 표시합니다.")

    col1, col2, col3, col4 = st.columns(4)

    total_tasks = len(tasks)
    completed_tasks = len(tasks[tasks["status"] == "완료"]) if len(tasks) > 0 else 0
    urgent_tasks_count = len(tasks[(tasks["d_day"] >= 0) & (tasks["d_day"] <= 3)]) if len(tasks) > 0 else 0
    external_count = len(external)

    col1.metric("전체 일정 수", total_tasks)
    col2.metric("완료 일정 수", completed_tasks)
    col3.metric("마감 임박 일정", urgent_tasks_count)
    col4.metric("수집된 외부 일정 수", external_count)

    st.divider()

    st.subheader("📅 내 통합 일정표")

    if len(tasks) > 0:
        task_calendar = tasks.copy().sort_values("deadline")

        st.dataframe(
            task_calendar[
                [
                    "deadline", "d_day", "type", "subject", "task_name",
                    "importance", "status", "created_date", "completed_date", "memo"
                ]
            ],
            use_container_width=True
        )
    else:
        st.info("아직 등록된 일정이 없습니다.")

    st.divider()

    st.subheader("🗓️ 날짜별 캘린더")

    if len(tasks) > 0:
        calendar_data = tasks.copy()
        calendar_data["deadline"] = pd.to_datetime(calendar_data["deadline"], errors="coerce")
        calendar_data = calendar_data.sort_values("deadline")

        unique_dates = calendar_data["deadline"].dt.date.unique()

        for day in unique_dates:
            st.markdown(f"### 📅 {day}")
            day_events = calendar_data[calendar_data["deadline"].dt.date == day]

            for _, row in day_events.iterrows():
                icon = "📚" if row["type"] == "과제" else "🏆"
                st.write(
                    f"{icon} **{row['task_name']}** / {row['type']} / {row['status']} / D-{row['d_day']}"
                )
    else:
        st.info("캘린더에 표시할 일정이 없습니다.")

    st.divider()

    st.subheader("🚨 마감 임박 내 일정 (D-3)")

    if len(tasks) > 0:
        urgent_tasks = tasks[(tasks["d_day"] >= 0) & (tasks["d_day"] <= 3)].sort_values("d_day")

        if len(urgent_tasks) > 0:
            st.dataframe(
                urgent_tasks[
                    ["deadline", "d_day", "type", "subject", "task_name", "importance", "status"]
                ],
                use_container_width=True
            )
        else:
            st.success("D-3 이내 마감 일정이 없습니다.")
    else:
        st.info("아직 등록된 일정이 없습니다.")


elif menu == "과제 등록":
    st.subheader("과제 등록")

    with st.form("task_form"):
        task_name = st.text_input("과제명")
        subject = st.text_input("과목명")
        deadline = st.date_input("마감일", value=date.today())
        importance = st.selectbox("중요도", ["높음", "보통", "낮음"])
        status = st.selectbox("진행 상태", ["시작 전", "진행 중", "완료"])
        memo = st.text_area("메모")

        submitted = st.form_submit_button("등록")

        if submitted:
            if task_name.strip() == "":
                st.warning("과제명을 입력해주세요.")
            else:
                today_str = pd.Timestamp.today().strftime("%Y-%m-%d")
                completed_date = today_str if status == "완료" else ""

                new_task = pd.DataFrame([{
                    "task_name": task_name,
                    "subject": subject,
                    "deadline": deadline.strftime("%Y-%m-%d"),
                    "importance": importance,
                    "status": status,
                    "memo": memo,
                    "type": "과제",
                    "created_date": today_str,
                    "completed_date": completed_date
                }])

                tasks = pd.concat([tasks, new_task], ignore_index=True)
                save_tasks(tasks)
                st.success("과제가 등록되었습니다!")


elif menu == "과제 목록":
    st.subheader("과제 목록")

    if len(tasks) == 0:
        st.info("아직 등록된 일정이 없습니다.")
    else:
        tasks = add_d_day(tasks)

        type_filter = st.selectbox("유형별 필터", ["전체", "과제", "공모전"])
        status_filter = st.selectbox("상태별 필터", ["전체", "시작 전", "진행 중", "완료", "마감 임박"])

        filtered_tasks = tasks.copy()

        if type_filter != "전체":
            filtered_tasks = filtered_tasks[filtered_tasks["type"] == type_filter]

        if status_filter != "전체":
            if status_filter == "마감 임박":
                filtered_tasks = filtered_tasks[
                    (filtered_tasks["d_day"] >= 0) & (filtered_tasks["d_day"] <= 3)
                ]
            else:
                filtered_tasks = filtered_tasks[filtered_tasks["status"] == status_filter]

        filtered_tasks = filtered_tasks.sort_values("d_day").reset_index(drop=True)

        st.dataframe(filtered_tasks, use_container_width=True)

        st.divider()

        st.subheader("✏️ 일정 상태 수정")

        if len(filtered_tasks) > 0:
            selected_task = st.selectbox(
                "상태를 변경할 일정 선택",
                filtered_tasks["task_name"].tolist()
            )

            selected_indices = tasks.index[tasks["task_name"] == selected_task].tolist()
            selected_idx = selected_indices[0]

            current_status = tasks.loc[selected_idx, "status"]

            status_options = ["시작 전", "진행 중", "완료"]

            new_status = st.selectbox(
                "변경할 상태",
                status_options,
                index=status_options.index(current_status) if current_status in status_options else 0
            )

            if st.button("상태 변경"):
                tasks.loc[selected_idx, "status"] = new_status

                if new_status == "완료":
                    tasks.loc[selected_idx, "completed_date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
                else:
                    tasks.loc[selected_idx, "completed_date"] = ""

                save_tasks(tasks)
                st.success("상태가 변경되었습니다.")
                st.rerun()

            st.divider()

            st.subheader("🗑️ 일정 삭제")

            delete_task = st.selectbox(
                "삭제할 일정 선택",
                filtered_tasks["task_name"].tolist(),
                key="delete_task"
            )

            if st.button("일정 삭제"):
                delete_indices = tasks.index[tasks["task_name"] == delete_task].tolist()
                delete_idx = delete_indices[0]

                tasks = tasks.drop(index=delete_idx).reset_index(drop=True)
                save_tasks(tasks)
                st.success("일정이 삭제되었습니다.")
                st.rerun()


elif menu == "외부 일정 탐색":
    st.write("위비티에서 사전 수집한 공모전/대외활동 데이터를 탐색할 수 있습니다.")

    keyword = st.text_input("검색어 입력", "")

    min_day = st.slider(
        "마감일까지 남은 기한",
        min_value=0,
        max_value=100,
        value=30
    )

    status_only = st.checkbox("접수중 일정만 보기", value=True)

    category_options = sorted(external["category"].dropna().unique())
    selected_category = st.selectbox("카테고리 선택", ["전체"] + category_options)

    filtered = external.copy()
    filtered = filtered[filtered["d_day"] >= min_day]

    if status_only:
        filtered = filtered[filtered["status"] == "접수중"]

    if keyword:
        filtered = filtered[
            filtered["title"].str.contains(keyword, case=False, na=False)
            | filtered["category"].str.contains(keyword, case=False, na=False)
            | filtered["organization"].str.contains(keyword, case=False, na=False)
        ]

    if selected_category != "전체":
        filtered = filtered[filtered["category"] == selected_category]

    filtered = filtered.sort_values("d_day").reset_index(drop=True)

    st.metric("검색 결과 수", len(filtered))

    st.dataframe(
        filtered[
            ["title", "category", "organization", "deadline", "d_day", "status", "url"]
        ],
        use_container_width=True
    )

    st.divider()

    st.subheader("📌 외부 일정을 내 일정에 추가")

    if len(filtered) > 0:
        selected_index = st.number_input(
            "추가할 일정 번호를 입력하세요",
            min_value=0,
            max_value=len(filtered) - 1,
            value=0,
            step=1
        )

        selected_row = filtered.iloc[selected_index]

        st.write("선택한 일정:")
        st.write(f"**{selected_row['title']}**")
        st.write(f"마감일: {selected_row['deadline'].date()} / D-{selected_row['d_day']}")
        st.write(f"주최기관: {selected_row['organization']}")
        st.write(f"상세 링크: {selected_row['url']}")

        if st.button("내 일정에 추가"):
            existing_titles = tasks["task_name"].tolist()

            if selected_row["title"] in existing_titles:
                st.warning("이미 내 일정에 추가된 항목입니다.")
            else:
                today_str = pd.Timestamp.today().strftime("%Y-%m-%d")

                new_task = pd.DataFrame([{
                    "task_name": selected_row["title"],
                    "subject": "외부 일정",
                    "deadline": selected_row["deadline"].strftime("%Y-%m-%d"),
                    "importance": "보통",
                    "status": "시작 전",
                    "memo": selected_row["url"],
                    "type": "공모전",
                    "created_date": today_str,
                    "completed_date": ""
                }])

                tasks = pd.concat([tasks, new_task], ignore_index=True)
                save_tasks(tasks)

                st.success("내 일정에 추가되었습니다.")
    else:
        st.info("추가할 외부 일정이 없습니다.")


elif menu == "추천":
    st.header("🎯 추천 외부 일정")

    tasks_recommend = add_d_day(tasks) if len(tasks) > 0 else tasks.copy()

    urgent_count = 0

    if len(tasks_recommend) > 0:
        urgent_count = len(
            tasks_recommend[
                (tasks_recommend["d_day"] >= 0) &
                (tasks_recommend["d_day"] <= 7)
            ]
        )

    st.metric("이번 주 마감 내 일정 수", urgent_count)

    if urgent_count >= 3:
        st.warning("이번 주 마감 일정이 많습니다. 새로운 외부 일정 참여는 신중히 고려하는 것이 좋습니다.")
    else:
        st.success("현재 일정에 비교적 여유가 있습니다.")

        recommended = external[
            (external["d_day"] >= 30) &
            (external["status"] == "접수중")
        ].sort_values("d_day").head(10)

        st.subheader("📌 마감까지 30일 이상 남은 추천 일정")

        st.dataframe(
            recommended[
                ["title", "category", "organization", "deadline", "d_day", "status", "url"]
            ],
            use_container_width=True
        )

    st.divider()

    st.subheader("추천 기준")
    st.write("""
    - 내 일정 중 D-7 이내 마감 일정이 3개 미만이면 비교적 여유가 있다고 판단합니다.
    - 접수중인 외부 일정만 추천합니다.
    - 준비 기간을 확보하기 위해 D-30 이상 남은 일정을 우선 추천합니다.
    """)


elif menu == "통계":
    st.header("📊 내 과제 수행 습관 분석")

    tasks_analysis = add_d_day(tasks) if len(tasks) > 0 else tasks.copy()

    st.write("""
    이 페이지에서는 사용자가 등록한 과제 데이터를 바탕으로
    과제 진행 상태, 과목별 과제 수, 과제 등록 시점, 과제 완료 시점을 분석합니다.
    """)

    if len(tasks_analysis) == 0:
        st.info("아직 등록된 일정이 없습니다. 과제를 등록하면 통계가 표시됩니다.")

    else:
        only_tasks = tasks_analysis[tasks_analysis["type"] == "과제"].copy()

        col1, col2, col3 = st.columns(3)
        col1.metric("등록된 과제 수", len(only_tasks))
        col2.metric("완료 과제 수", len(only_tasks[only_tasks["status"] == "완료"]))
        col3.metric("진행 중 과제 수", len(only_tasks[only_tasks["status"] == "진행 중"]))

        st.divider()

        st.subheader("1️⃣ 과제 상태 비율")

        status_count = only_tasks["status"].value_counts()

        if len(status_count) > 0:
            draw_pie_chart(status_count, "과제 상태 비율")
            st.write("현재 등록된 과제들이 시작 전, 진행 중, 완료 상태에 어떻게 분포하는지 보여줍니다.")
            st.dataframe(status_count)
        else:
            st.info("과제 데이터가 없습니다.")

        st.divider()

        st.subheader("2️⃣ 과목별 과제 비율")

        subject_count = only_tasks["subject"].value_counts()

        if len(subject_count) > 0:
            draw_pie_chart(subject_count, "과목별 과제 비율")
            st.write("어떤 과목에 과제가 많이 몰려 있는지 확인할 수 있습니다.")
            st.dataframe(subject_count)
        else:
            st.info("과목 정보가 있는 과제가 없습니다.")

        st.divider()

        st.subheader("3️⃣ 내 일정 마감일 타임라인")

        if len(only_tasks) > 0:
            draw_timeline(only_tasks)
            st.write("앞으로 2개월 안에 등록한 과제들이 어느 날짜에 몰려 있는지 확인할 수 있습니다.")
        else:
            st.info("타임라인을 그릴 과제가 없습니다.")

        st.divider()

        st.subheader("4️⃣ 과제 등록 시점 분석")

        only_tasks["deadline"] = pd.to_datetime(only_tasks["deadline"], errors="coerce")
        only_tasks["created_date"] = pd.to_datetime(only_tasks["created_date"], errors="coerce")

        only_tasks["days_registered_before_deadline"] = (
            only_tasks["deadline"] - only_tasks["created_date"]
        ).dt.days

        registered_data = only_tasks["days_registered_before_deadline"].dropna()

        if len(registered_data) > 0:
            avg_registered = registered_data.mean()

            st.metric("평균 과제 등록 시점", f"마감 {avg_registered:.1f}일 전")

            draw_histogram(
                registered_data,
                "과제를 마감 며칠 전에 등록했는가",
                "마감 전 등록 일수",
                "과제 수"
            )

            st.write("이 그래프는 사용자가 과제를 얼마나 여유 있게 등록하는지 보여줍니다.")
        else:
            st.info("등록 시점 분석에 사용할 데이터가 없습니다.")

        st.divider()

        st.subheader("5️⃣ 과제 완료 시점 분석")

        completed_tasks_df = only_tasks[
            (only_tasks["status"] == "완료") &
            (only_tasks["completed_date"].notna()) &
            (only_tasks["completed_date"] != "")
        ].copy()

        if len(completed_tasks_df) > 0:
            completed_tasks_df["completed_date"] = pd.to_datetime(
                completed_tasks_df["completed_date"],
                errors="coerce"
            )

            completed_tasks_df["days_completed_before_deadline"] = (
                completed_tasks_df["deadline"] - completed_tasks_df["completed_date"]
            ).dt.days

            completed_data = completed_tasks_df["days_completed_before_deadline"].dropna()

            avg_completed = completed_data.mean()

            st.metric("평균 과제 완료 시점", f"마감 {avg_completed:.1f}일 전")

            draw_histogram(
                completed_data,
                "과제를 마감 며칠 전에 완료했는가",
                "마감 전 완료 일수",
                "과제 수"
            )

            st.write("이 그래프는 사용자가 과제를 마감 전에 얼마나 여유 있게 완료하는지 보여줍니다.")

            st.write("완료 과제 상세 데이터")
            st.dataframe(
                completed_tasks_df[
                    [
                        "task_name", "subject", "deadline", "created_date",
                        "completed_date", "days_completed_before_deadline"
                    ]
                ],
                use_container_width=True
            )
        else:
            st.info("완료된 과제가 아직 없습니다. 과제 상태를 '완료'로 변경하면 완료 시점 분석이 표시됩니다.")

        st.divider()

        st.subheader("📌 분석 결과 요약")

        most_status = status_count.index[0] if len(status_count) > 0 else "없음"
        most_subject = subject_count.index[0] if len(subject_count) > 0 else "없음"
        avg_registered_text = f"{registered_data.mean():.1f}일 전" if len(registered_data) > 0 else "분석 불가"

        st.markdown(f"""
        - 현재 가장 많은 과제 상태는 **{most_status}**입니다.
        - 과제가 가장 많이 등록된 과목은 **{most_subject}**입니다.
        - 평균적으로 과제는 마감 **{avg_registered_text}** 등록되었습니다.
        - 완료된 과제가 있는 경우, 마감 며칠 전에 완료하는 경향이 있는지 확인할 수 있습니다.
        """)


elif menu == "데이터 설명":
    st.subheader("데이터 수집 방법")
    st.write("""
    본 프로젝트에서는 BeautifulSoup를 활용하여 위비티(WEVITY)의 공모전/대외활동 정보를 사전에 수집했습니다.
    웹앱에서는 실시간 크롤링을 수행하지 않고, 저장된 CSV 파일을 불러와 분석과 시각화에 활용합니다.
    """)

    st.subheader("수집 데이터 항목")
    st.write("""
    - 공모전/대외활동명
    - 분야
    - 주최기관
    - 마감일
    - 접수상태
    - 상세 링크
    - 데이터 출처
    """)

    st.subheader("분석 방법")
    st.write("""
    수집된 외부 일정 데이터는 pandas를 이용해 정제했습니다. 마감일을 날짜 형식으로 변환하고,
    현재 날짜를 기준으로 D-day를 계산했습니다.

    또한 사용자가 직접 등록한 과제 데이터에는 등록일과 완료일을 저장하여,
    과제를 마감 며칠 전에 등록했는지, 마감 며칠 전에 완료했는지를 분석했습니다.
    """)

    st.subheader("분석 결과 설명")
    st.write("""
    통계 페이지에서는 과제 상태 비율, 과목별 과제 비율, 앞으로 2개월 내 과제 마감일 타임라인,
    과제 등록 시점, 과제 완료 시점을 확인할 수 있습니다.
    이를 통해 사용자가 과제를 언제 등록하고, 언제 완료하는지 자신의 수행 습관을 파악할 수 있습니다.
    """)

    st.subheader("웹앱 주요 기능")
    st.write("""
    - 사용자가 직접 과제를 등록하고 D-day를 확인할 수 있습니다.
    - 수집된 외부 일정을 검색, 필터링할 수 있습니다.
    - 관심 있는 외부 일정을 내 일정에 추가하여 과제와 함께 관리할 수 있습니다.
    - 홈 화면의 캘린더에서 과제와 외부활동을 함께 확인할 수 있습니다.
    - 일정 상태를 시작 전, 진행 중, 완료로 변경할 수 있습니다.
    - 현재 일정 여유도에 따라 참여 가능한 외부 일정을 추천합니다.
    - 완료된 과제를 바탕으로 과제 수행 습관을 분석합니다.
    """)