import matplotlib.pyplot as plt
import asyncio
import sys
from decimal import Decimal
from pathlib import Path

import streamlit as st

# ----------------------------------------------------
# Make src/ importable
# ----------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from payment_router.core.fx import supported_currencies
from payment_router.core.graph import PaymentGraph
from payment_router.router import PaymentRouter, RoutingPreference

from payment_router.networks.wise import WiseNetwork
from payment_router.networks.swift import SWIFTNetwork
from payment_router.networks.sepa import SEPANetwork

st.set_page_config(
    page_title="Payment Routing Simulator",
    page_icon="💸",
    layout="wide",
)

st.title("💸 AI Payment Routing Simulator")

st.caption(
    "Find the fastest and cheapest international payment route using graph algorithms."
)

st.write("Find the best payment route between two currencies.")

st.divider()

currencies = sorted(list(supported_currencies()))

col1, col2 = st.columns(2)

with col1:
    source = st.selectbox(
        "Source Currency",
        currencies,
    )

with col2:
    target = st.selectbox(
        "Target Currency",
        currencies,
        index=currencies.index("INR"),
    )


amount = st.number_input(
    "Amount",
    min_value=1.0,
    value=100.0,
    step=10.0,
)

preference = st.selectbox(
    "Routing Preference",
    [
        "Cheapest",
        "Fastest",
        "Balanced",
    ],
)
run = st.button("🚀 Find Best Route")
if run:

    if preference == "Cheapest":
        routing_preference = RoutingPreference(
            cost_weight=1.0,
            time_weight=0.0,
        )

    elif preference == "Fastest":
        routing_preference = RoutingPreference(
            cost_weight=0.0,
            time_weight=1.0,
        )

    else:
        routing_preference = RoutingPreference(
            cost_weight=0.5,
            time_weight=0.5,
        )

    networks = [
        WiseNetwork(),
        SWIFTNetwork(),
        SEPANetwork(),
    ]

    graph = PaymentGraph(
        networks=networks,
        currencies=currencies,
        amount=Decimal(str(amount)),
    )

    asyncio.run(graph.build())

    router = PaymentRouter(graph)

    route = router.find_route(
        source,
        target,
        Decimal(str(amount)),
        routing_preference,
    )
    if route is None:

        st.error("No route found.")

    else:

        st.success("Route Found!")

        st.subheader("📍 Best Route")

    path = " → ".join(
    [route.source_currency]
    + [hop.to_node for hop in route.hops]
    )

    st.info(f"📍 **Route:** {path}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
        "💰 Total Fee",
        f"${route.total_fee_usd:.2f}"
    )

    with col2:
        st.metric(
        "⏱ Time",
        f"{route.total_time_hours:.2f} hrs"
        )

    with col3:
        st.metric(
        f"💵 Final Amount ({route.target_currency})",
        f"{route.final_amount:.2f}"
        )

    with col4:
        st.metric(
        "🛣 Hops",
        len(route.hops)
        )
    st.subheader("🏦 Selected Network")

    st.success(route.hops[0].network_name.upper())
    st.divider()

    st.subheader("Hop Breakdown")
    for i, hop in enumerate(route.hops, start=1):

        with st.expander(f"Hop {i}"):

            st.write(f"**Network:** {hop.network_name}")

            st.write(
            f"**Pair:** {hop.from_node} → {hop.to_node}"
            )

            st.write(
            f"**Fee:** ${hop.fee_usd}"
            )

            st.write(
            f"**Time:** {hop.time_hours} hours"
            )

            st.write(
            f"**Exchange Rate:** {hop.fx_rate}"
            )

            st.write(
            f"**Data Source:** {hop.data_source.value}"
            )
    st.divider()

    st.subheader("📊 Route Analytics")

    fees = [float(hop.fee_usd) for hop in route.hops]
    labels = [hop.network_name for hop in route.hops]

    fig, ax = plt.subplots()

    ax.pie(
        fees,
        labels=labels,
        autopct="%1.1f%%"
    )

    st.pyplot(fig)
    times = [float(hop.time_hours) for hop in route.hops]

    fig2, ax2 = plt.subplots()

    ax2.bar(labels, times)

    ax2.set_ylabel("Hours")

    st.pyplot(fig2)

    st.divider()

    st.caption("Developed by Chahat Singh | Python • NetworkX • Streamlit • Graph Algorithms")