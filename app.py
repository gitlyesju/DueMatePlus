import streamlit as st
import pandas as pd
import os
from datetime import date
import altair as alt

st.set_page_config(page_title="DueMate+", layout="wide")

TASK_FILE = "data/my_tasks.csv"
EXTERNAL_FILE = "data/external_deadlines.csv"

st.title("📚 DueMate+")
st.subheader("대학생 과제 및 대외활동 통합 마감 관리 웹앱")


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

        text_cols = [
            "task_name", "subject", "importance", "status",
            "memo", "type", "created_date", "completed_date"
        ]

        for col in text_cols:
            df[col] = df[col].fillna("").astype(str)

        return df

    return pd.DataFrame(columns=columns)


def save_tasks(df):
    df = df.copy()

    text_cols = [
        "task_name", "subject", "importance", "status",
        "memo", "type", "created_date", "completed_date"
    ]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    df.to_csv(TASK_FILE, index=False, encoding="utf-8-sig")


def add_d_day(df, deadline_col="deadline"):
    df = df.copy()
    df[deadline_col] = pd.to_datetime(df[deadline_col], errors="coerce")
    today = pd.Timestamp.today().normalize()
    df["d_day"] = (df[deadline_col] - today).dt.days
    return df


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

    st.caption("마감 임박 기준: 내 일정은 D-3 이내로 표시합니다. 완료된 일정은 홈 화면에서 제외됩니다.")

    if len(tasks) > 0:
        active_tasks = tasks[tasks["status"].astype(str).str.strip() != "완료"].copy()
    else:
        active_tasks = tasks.copy()

    col1, col2, col3, col4 = st.columns(4)

    total_tasks = len(tasks)
    active_count = len(active_tasks)
    completed_tasks = len(tasks[tasks["status"].astype(str).str.strip() == "완료"]) if len(tasks) > 0 else 0
    urgent_tasks_count = len(
        active_tasks[(active_tasks["d_day"] >= 0) & (active_tasks["d_day"] <= 3)]
    ) if len(active_tasks) > 0 else 0

    col1.metric("전체 일정 수", total_tasks)
    col2.metric("진행 중 일정 수", active_count)
    col3.metric("완료 일정 수", completed_tasks)
    col4.metric("마감 임박 일정", urgent_tasks_count)

    st.divider()

    st.subheader("📅 내 통합 일정표")

    if len(active_tasks) > 0:
        task_calendar = active_tasks.copy().sort_values("deadline")

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
        st.info("현재 진행 중인 일정이 없습니다.")

    st.divider()

    st.subheader("🗓️ 날짜별 캘린더")

    if len(active_tasks) > 0:
        calendar_data = active_tasks.copy()
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
        st.info("캘린더에 표시할 진행 중 일정이 없습니다.")

    st.divider()

    st.subheader("🚨 마감 임박 내 일정 (D-3)")

    if len(active_tasks) > 0:
        urgent_tasks = active_tasks[
            (active_tasks["d_day"] >= 0) & (active_tasks["d_day"] <= 3)
        ].sort_values("d_day")

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
        st.info("현재 진행 중인 일정이 없습니다.")


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
                (tasks_recommend["d_day"] <= 7) &
                (tasks_recommend["status"] != "완료")
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
    - 완료되지 않은 내 일정 중 D-7 이내 마감 일정이 3개 미만이면 비교적 여유가 있다고 판단합니다.
    - 접수중인 외부 일정만 추천합니다.
    - 준비 기간을 확보하기 위해 D-30 이상 남은 일정을 우선 추천합니다.
    """)


elif menu == "통계":
    st.header("📊 과제 수행 기간 분석")

    tasks_analysis = add_d_day(tasks) if len(tasks) > 0 else tasks.copy()

    if len(tasks_analysis) == 0:
        st.info("아직 등록된 일정이 없습니다. 과제를 등록하면 통계가 표시됩니다.")

    else:
        only_tasks = tasks_analysis[tasks_analysis["type"] == "과제"].copy()

        if len(only_tasks) == 0:
            st.info("등록된 과제가 없습니다.")

        else:
            only_tasks["deadline"] = pd.to_datetime(only_tasks["deadline"], errors="coerce")
            only_tasks["created_date"] = pd.to_datetime(only_tasks["created_date"], errors="coerce")

            only_tasks["deadline_minus_created"] = (
                only_tasks["deadline"] - only_tasks["created_date"]
            ).dt.days

            only_tasks = only_tasks.dropna(subset=["deadline_minus_created"])

            col1, col2, col3 = st.columns(3)

            col1.metric("등록된 과제 수", len(only_tasks))
            col2.metric("평균 확보 기간", f"{only_tasks['deadline_minus_created'].mean():.1f}일")
            col3.metric("가장 긴 확보 기간", f"{only_tasks['deadline_minus_created'].max():.0f}일")

            st.write("""
            이 그래프는 과제를 등록한 날부터 마감일까지 며칠의 여유가 있었는지를 보여줍니다.
            값이 클수록 사용자가 더 일찍 과제를 등록했다는 뜻입니다.
            """)

            chart_data = only_tasks[
                ["task_name", "subject", "deadline", "created_date", "deadline_minus_created", "status"]
            ].copy()

            chart_data["deadline_minus_created"] = chart_data["deadline_minus_created"].astype(float)

            chart = (
                alt.Chart(chart_data)
                .mark_circle(size=180)
                .encode(
                    x=alt.X(
                        "deadline_minus_created:Q",
                        title="과제 등록일부터 마감일까지 남은 일수"
                    ),
                    y=alt.Y(
                        "task_name:N",
                        title="과제명",
                        sort="-x"
                    ),
                    color=alt.Color(
                        "status:N",
                        title="진행 상태"
                    ),
                    tooltip=[
                        alt.Tooltip("task_name:N", title="과제명"),
                        alt.Tooltip("subject:N", title="과목"),
                        alt.Tooltip("status:N", title="상태"),
                        alt.Tooltip("created_date:T", title="등록일"),
                        alt.Tooltip("deadline:T", title="마감일"),
                        alt.Tooltip("deadline_minus_created:Q", title="확보 기간")
                    ]
                )
                .properties(
                    width=800,
                    height=max(300, len(chart_data) * 45),
                    title="과제별 등록일-마감일 확보 기간"
                )
            )

            rule = (
                alt.Chart(chart_data)
                .mark_rule(strokeDash=[4, 4])
                .encode(
                    x="mean(deadline_minus_created):Q"
                )
            )

            st.altair_chart(chart + rule, use_container_width=True)

            st.subheader("분석 결과 요약")

            avg_days = only_tasks["deadline_minus_created"].mean()
            min_task = only_tasks.loc[only_tasks["deadline_minus_created"].idxmin()]
            max_task = only_tasks.loc[only_tasks["deadline_minus_created"].idxmax()]

            st.markdown(f"""
            - 평균적으로 과제는 마감 **{avg_days:.1f}일 전** 등록되었습니다.
            - 가장 여유 있게 등록한 과제는 **{max_task['task_name']}**입니다.
            - 가장 늦게 등록한 과제는 **{min_task['task_name']}**입니다.
            - 이 분석을 통해 사용자는 자신이 과제를 얼마나 미리 관리하는지 확인할 수 있습니다.
            """)

            st.subheader("상세 데이터")
            st.dataframe(
                chart_data.sort_values("deadline_minus_created", ascending=False),
                use_container_width=True
            )


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
    수집된 외부 일정 데이터는 pandas를 이용해 정제했습니다.
    마감일을 날짜 형식으로 변환하고 현재 날짜를 기준으로 D-day를 계산했습니다.

    사용자가 직접 등록한 과제 데이터에는 등록일과 마감일을 저장했습니다.
    이를 바탕으로 과제 등록일부터 마감일까지 남은 일수를 계산하여
    사용자가 과제를 얼마나 미리 관리하는지 분석했습니다.
    """)

    st.subheader("분석 결과 설명")
    st.write("""
    통계 페이지에서는 과제별 등록일-마감일 확보 기간을 시각화합니다.
    이를 통해 사용자는 어떤 과제를 충분히 미리 등록했는지,
    어떤 과제를 마감에 가깝게 등록했는지 확인할 수 있습니다.
    """)

    st.subheader("웹앱 주요 기능")
    st.write("""
    - 사용자가 직접 과제를 등록하고 D-day를 확인할 수 있습니다.
    - 수집된 외부 일정을 검색, 필터링할 수 있습니다.
    - 관심 있는 외부 일정을 내 일정에 추가하여 과제와 함께 관리할 수 있습니다.
    - 홈 화면의 캘린더에서 과제와 외부활동을 함께 확인할 수 있습니다.
    - 완료된 일정은 홈 화면에서 제외되어 현재 해야 할 일만 확인할 수 있습니다.
    - 일정 상태를 시작 전, 진행 중, 완료로 변경할 수 있습니다.
    - 현재 일정 여유도에 따라 참여 가능한 외부 일정을 추천합니다.
    - 과제 등록일부터 마감일까지 확보한 기간을 분석합니다.
    """)
