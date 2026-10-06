let latencyHistory = [];
let timeHistory = [];

let latencyChart;


// ==========================================
// LOAD DATA DARI PYTHON
// ==========================================

async function loadMonitoringData() {

    try {

        const response = await fetch(
            "status.json?t=" + Date.now()
        );

        if (!response.ok) {
            throw new Error("status.json tidak ditemukan");
        }

        const data = await response.json();

        updateDashboard(data);

    } catch (error) {

        console.error(
            "Gagal mengambil data monitoring:",
            error
        );

    }

}


// ==========================================
// UPDATE DASHBOARD
// ==========================================

function updateDashboard(data) {

    const hosts = data.hosts || [];

    let online = 0;
    let offline = 0;

    let totalLatency = 0;
    let latencyCount = 0;


    // --------------------------------------
    // HOST CARD
    // --------------------------------------

    const container =
        document.getElementById("hostContainer");

    container.innerHTML = "";


    hosts.forEach(host => {

        if (host.status === "online") {

            online++;

            if (
                typeof host.response === "number"
            ) {

                totalLatency += host.response;

                latencyCount++;

            }

        } else {

            offline++;

        }


        const card =
            document.createElement("div");


        card.className =
            `host-card ${host.status}`;


        const statusText =
            host.status === "online"
                ? "ONLINE"
                : "OFFLINE";


        const responseText =
            host.response !== null &&
            host.response !== undefined
                ? `${host.response} ms`
                : "TIMEOUT";


        card.innerHTML = `

            <div class="host-header">

                <div>

                    <div class="host-name">
                        ${host.name}
                    </div>

                    <div class="host-type">
                        ${host.type}
                    </div>

                </div>


                <div class="status ${host.status}">
                    ${statusText}
                </div>

            </div>


            <div class="host-info">

                <div class="info-row">

                    <span>
                        Address
                    </span>

                    <strong>
                        ${host.address}
                    </strong>

                </div>


                <div class="info-row">

                    <span>
                        Response
                    </span>

                    <strong class="latency">
                        ${responseText}
                    </strong>

                </div>


                <div class="info-row">

                    <span>
                        Downtime
                    </span>

                    <strong class="downtime">
                        ${host.downtime}
                    </strong>

                </div>

            </div>

        `;


        container.appendChild(card);

    });


    // --------------------------------------
    // STATISTICS
    // --------------------------------------

    document.getElementById(
        "totalHost"
    ).textContent = hosts.length;


    document.getElementById(
        "onlineHost"
    ).textContent = online;


    document.getElementById(
        "offlineHost"
    ).textContent = offline;


    const average =
        latencyCount > 0
            ? Math.round(
                totalLatency / latencyCount
            )
            : 0;


    document.getElementById(
        "avgLatency"
    ).textContent = average;


    // --------------------------------------
    // LAST UPDATE
    // --------------------------------------

    document.getElementById(
        "lastUpdate"
    ).textContent =
        data.lastUpdate || "-";


    // --------------------------------------
    // UPDATE CHART
    // --------------------------------------

    updateChart(average);

}


// ==========================================
// CHART
// ==========================================

function updateChart(average) {

    const now =
        new Date().toLocaleTimeString(
            "id-ID",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        );


    timeHistory.push(now);
    latencyHistory.push(average);


    // Simpan maksimal 20 titik
    if (timeHistory.length > 20) {

        timeHistory.shift();
        latencyHistory.shift();

    }


    if (!latencyChart) {

        const ctx =
            document.getElementById(
                "latencyChart"
            );


        latencyChart =
            new Chart(ctx, {

                type: "line",

                data: {

                    labels: timeHistory,

                    datasets: [

                        {

                            label:
                                "Average Response Time",

                            data:
                                latencyHistory,

                            borderColor:
                                "#4da3ff",

                            backgroundColor:
                                "rgba(77,163,255,0.08)",

                            borderWidth: 2,

                            fill: true,

                            tension: 0.4,

                            pointRadius: 3,

                            pointBackgroundColor:
                                "#4da3ff"

                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,


                    plugins: {

                        legend: {
                            display: false
                        }

                    },


                    scales: {

                        x: {

                            grid: {

                                color:
                                    "rgba(255,255,255,0.04)"

                            },

                            ticks: {

                                color:
                                    "#667383",

                                font: {
                                    size: 9
                                }

                            }

                        },


                        y: {

                            beginAtZero: true,

                            grid: {

                                color:
                                    "rgba(255,255,255,0.04)"

                            },

                            ticks: {

                                color:
                                    "#667383",

                                font: {
                                    size: 9
                                },

                                callback:
                                    function(value) {

                                        return value +
                                            " ms";

                                    }

                            }

                        }

                    }

                }

            });

    }

    else {

        latencyChart.data.labels =
            timeHistory;

        latencyChart.data.datasets[0].data =
            latencyHistory;

        latencyChart.update();

    }

}


// ==========================================
// JAM REAL-TIME
// ==========================================

function updateClock() {

    const now =
        new Date();

    document.getElementById(
        "clock"
    ).textContent =
        now.toLocaleTimeString(
            "id-ID"
        );

}


setInterval(
    updateClock,
    1000
);

updateClock();


// ==========================================
// LOAD DATA SETIAP 5 DETIK
// ==========================================

loadMonitoringData();

setInterval(
    loadMonitoringData,
    5000
);