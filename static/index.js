const {LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine} = Recharts;
function HeaterStages (props) {
    return (
        <div className="box">
            {
            props.heating_stages && props.heating_stages.length > 0 &&
            <table className="table is-striped is-narrow is-hoverable is-fullwidth">
                <thead>
                    <tr>
                       <th>Name</th>
                       <th>Time</th>
                       <th>Temp</th>
                       <th><abbr title="Time remaining">T.R</abbr></th>
                       <th>Controls</th>
                    </tr>
                </thead>
                <tbody>
                {
                props.heating_stages &&
                props.heating_stages.map((stage, index) => {
                    return (
                            <tr className={stage.active ? "is-selected" : ""}>
                                <td>{stage.name}</td>
                                <td>{stage.time}</td>
                                <td>{stage.temp}</td>
                                <td>{stage.time_remaining}</td>
                                <td>
                                    <a className="button is-small"
                                       onClick={props.handleEnableClick}>
                                        <span className="icon is-medium">
                                            <i className="fas fa-trash" />
                                        </span>
                                    </a>
                                <a className="button is-small"
                                   onClick={props.handleEnableClick}>
                                    <span className="icon is-medium">
                                        <i className="fas fa-edit" />
                                    </span>
                                </a>
                                </td>
                            </tr>
                    )
                })
                }
                </tbody>
            </table>
            }
            <a className="button is-large"
               onClick={() => { props.handleAutomationStateChangeReq("STARTED")}}>
                <span className="icon is-medium">
                    <i className="fas fa-play" />
                </span>
            </a>
            <a className="button is-large"
               onClick={props.handleEnableClick}>
                <span className="icon is-medium">
                    <i className="fas fa-plus-square" />
                </span>
            </a>
        </div>
    )
}

class VesselControl extends React.Component {
    constructor (props) {
        super(props);

        this.state = {
            "active": false,
            "is_manual": false,
            "level": 0.0,
            "mode": "off",
            "pid": {"setpoint": 0}
        };

        this.props.es.addEventListener("vessel-heater-" + props.id, e => {
            this.setState(JSON.parse(e.data))
        });

        this.setpointInputRef = React.createRef();
    }

    componentDidMount() {
        const field = this.setpointInputRef.current;
        field.value = this.state.pid.setpoint;
    }

    render() {
        const setpointChanged = (e) => {
            const new_temp = e.target.value

            putVessel("setpoint", this.props.id, {"temperature": parseInt(new_temp)}, () => {});
        };

        const modifySetpoint = (modifier) => {
            const field = this.setpointInputRef.current
            field.value = parseInt(field.value) + modifier;

            setpointChanged({"target": field});
        };

        const handleEnableClick = () => {
            console.log(this.state.mode);
            var new_mode = "PID";

            if (this.state.mode.mode == "ON" || this.state.mode.mode == "PID") {
                new_mode = "OFF";
            }

            putVessel("mode", this.props.id, {"mode": new_mode}, () => {});
        };

        return (
            <div className="box has-text-centered">
                <div className="field has-addons">
                    <a className="button is-large"
                       onClick={handleEnableClick}>
                        <span className={"icon is-medium " + (this.state.mode.mode != "OFF" ? "has-text-danger" : "")}
                              >
                            <i className="fas fa-power-off" />
                        </span>
                    </a>
                    &nbsp;
                    &nbsp;
                    <input className="control input is-large is-expanded"
                           style={{width: "7em"}}
                           type="text"
                           placeholder={this.state.pid.setpoint.temperature}
                           onChange={setpointChanged}
                           ref = {this.setpointInputRef}
                    />

                    <p className="control" onClick={() => modifySetpoint(10)}>
                        <button className="button is-large">
                            <i className="fas fa-angle-double-up" />
                        </button>
                    </p>
                    <p className="control" onClick={() => modifySetpoint(1)}>
                        <button className="button is-large">
                            <i className="fas fa-angle-up" />
                        </button>
                    </p>
                    <p className="control" onClick={() => modifySetpoint(-1)}>
                        <button className="button is-large">
                            <i className="fas fa-angle-down" />
                        </button>
                    </p>
                    <p className="control" onClick={() => modifySetpoint(-10)}>
                        <button className="button is-large">
                            <i className="fas fa-angle-double-down" />
                        </button>
                    </p>
                    <p className="control">
                        <button className="button is-static is-large">
                            &#8451;
                        </button>
                    </p>
                </div>
            </div>
        );
    }
}

function Pump (props) {
    return (
        <div className="box has-text-centered">
            <div>
                <p className="heading">{props.pump.name}</p>
                <a className="button is-large"
                   onClick={props.handleClick}>
                    <span className={"icon is-medium " + (props.pump.active ? "has-text-danger" : "")}
                          >
                        <i className="fas fa-retweet" />
                    </span>
                </a>
            </div>
        </div>
    );
}

class SimpleLineChart extends React.Component {
    constructor (props) {
        super(props);
        const MAX_CHART_SIZE = 500
        this.state = {"chart": []};

        this.props.es.addEventListener("vessel-chart-" + props.id, e => {
            var newChart = []
            if (this.state.chart.length >= MAX_CHART_SIZE) {
                const boundedChart = this.state.chart.slice(1,MAX_CHART_SIZE)
                newChart = boundedChart.concat(JSON.parse(e.data))
            } else {
                newChart = this.state.chart.concat(JSON.parse(e.data))
            }

            this.setState({"chart": newChart})
        });
    }

    render () {
        const tickFormatter = (time) => {
            return new Date(time * 1e3).toISOString().slice(-13, -5);
        };

        let temp = (t) => {return t.temperature.temperature};
        let sp = (t) => {return t.setpoint.temperature};
        let heater_level = (t) => {return t.heater_level.power};

        return (
            <LineChart width={760} height={350} data={this.state.chart}>
               <XAxis dataKey="date" tickFormatter={tickFormatter} angle={-45} textAnchor="end" height={65}/>
               <YAxis />
               <YAxis yAxisId="right" orientation="right" />
               <CartesianGrid strokeDasharray="3 3"/>
               <Line type="monotone" dataKey={temp} stroke="#8884d8" isAnimationActive={false} dot={false} type="number"/>
               <Line type="monotone" dataKey={sp} stroke="red" strokeDasharray="3 3" isAnimationActive={false} dot={false}/>
               <Line yAxisId="right" type="monotone" dataKey={heater_level} stroke="#84d895" isAnimationActive={false} dot={false}/>
          </LineChart>
        );
    }
}

class HeatGauge extends React.Component {
    constructor (props) {
        super(props);
        this.state = {"output": -1};

        this.props.es.addEventListener("vessel-power-" + props.id, e => {
            this.setState({"output": JSON.parse(e.data)})
        });
    }

    render () {
        var color = "is-primary";

        return (
            <progress
            className={"progress " + color}
            value={this.state.output}
            max="100" />
        );
    }
}

class TemperatureLabel extends React.Component {
    constructor (props) {
        super(props);

        this.state = {
            "temperature": "?",
            "unit": "C"
        };

        this.props.es.addEventListener("vessel-temperature-" + props.id, e => {
            this.setState(JSON.parse(e.data))
        });
    }

    render () {
        return (
            <div>
                <p className="heading">{this.props.name}</p>
                <p className="title">{this.state.temperature}&#xB0;{this.state.unit}</p>
            </div>
        );
    }
}

class Vessel extends React.Component {
    constructor (props) {
        super(props);
        this.state = {
            "id": props.id,
            "name": "Unknown"
        };

        this.props.es.addEventListener("vessel-" + props.id, e => {
            this.setState(JSON.parse(e.data))
        });
    }

    render() {
        const setpointChanged = (e) => {
            console.log(e)
        }

        return (
            <div className="has-text-centered">
                <div className="box">
                    <TemperatureLabel name={this.state.name} id={this.state.id} es={this.props.es}/>
                    <HeatGauge id={this.state.id} es={this.props.es}/>
                    <SimpleLineChart id={this.state.id} es={this.props.es}/>
                    <VesselControl setpointChanged={setpointChanged}
                                   id={this.state.id}
                                   es={this.props.es}/>
                </div>
            </div>
        );
    }
}

class ControlPanel extends React.Component {
    constructor (props) {
        super(props);
        this.state = {"vessels": []};

        this.eventSource = new EventSource("/v1/stream");
        this.eventSource.addEventListener("vessels", e => {
            this.setState({"vessels": JSON.parse(e.data)})
        });
    }

    render() {
        return (
            <div>
            {
                this.state.vessels.map((vessel, i) => {
                    return (<Vessel id={vessel} key={vessel} es={this.eventSource}/>)
                })
            }
            </div>
        );
    }
}

ReactDOM.render(
  <ControlPanel />,
  document.getElementById('root')
);

function putVessel(func, vesselId, data, cb) {
    console.log("putVessel");
    return axios
        .put("/v1/vessel/" + vesselId + "/" + func, data)
        .then((response) => {
            cb (response.data)
        }).catch(function (error) {
            console.log(error);
        });
}

function fetchVessels(cb) {
    return axios.get("/v1/vessel")
    .then(function (response) {
        cb(response);
    }).catch(function (error) {
        console.log(error);
    });
}

function setHeaterActiveState(id, state, cb) {
    return axios
        .put("/state/heater/" + id,
             {"active": state}
        ).then((response) => {cb (response.data)})
        .catch(function (error) {
            console.log(error);
        });
}

function setHeaterEnabledState(heater, enabled, cb) {
    return axios
        .put("/state/heater/" + heater,
             {"enabled": enabled}
        ).then((response) => {cb (response.data)})
        .catch(function (error) {
            console.log(error);
        });
}

function setHeaterSetpoint(heater, setpoint, cb) {
    return axios
        .put("/state/heater/" + heater,
             {"setpoint": setpoint}
        ).then((response) => {cb (response.data)})
        .catch(function (error) {
            console.log(error);
        });
}

function setSensorAutomationState(sensor, new_state, cb) {
    return axios
        .put("/state/sensor/" + sensor,
             {"automation_state": new_state}
        ).then((response) => {cb (response.data)})
        .catch(function (error) {
            console.log(error);
        });
}

function setPump(pump, state) {
    return setActiveState("pump", pump, state);
}

function setHeater(heater, state) {
    return setActiveState("heater", heater, state);
}
