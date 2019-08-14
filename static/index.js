const {LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine} = Recharts;

function Heater (props) {
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

    return (
        <div className="box has-text-centered">
            <p className="heading">{props.heater.name}</p>
            <div className="field has-addons">
                <a className="button is-large"
                   onClick={props.handleEnableClick}>
                    <span className={"icon is-medium " + (props.heater.enabled ? "has-text-danger" : "")}
                          >
                        <i className="fas fa-power-off" />
                    </span>
                </a>
                &nbsp;
                &nbsp;
                { props.heater.is_manual &&
                    <div>
                        <a className="button is-large"
                           onClick={props.handleActivateClick}>
                            <span className={"icon is-medium " + (props.heater.active ? "has-text-danger" : "")}
                                  >
                                <i className="fas fa-fire" />
                            </span>
                        </a>
                    </div>
                }
                { !props.heater.is_manual &&
                    <input className="control input is-large is-expanded"
                           style={{width: "7em"}}
                           type="text"
                           placeholder={props.setpoint}
                           onChange={props.setpointChanged}
                    />
                }
                { !props.heater.is_manual &&
                    <p className="control">
                        <button className="button is-static is-large">
                            &#8451;
                        </button>
                    </p>
                }
            </div>
            <HeaterStages heating_stages={props.heating_stages}
                          handleAutomationStateChangeReq={props.handleAutomationStateChangeReq}/>
        </div>
    );
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

function Sensor (props) {
    function HeatIcon (props) {
        return (
                <span className={"icon is-large " + (props.active ? "has-text-danger" : "")}>
                    <i className="fas fa-3x fa-fire" />
                </span>
        );
    }

    function HeatGauge (props) {
        var color = "is-primary";

        if (props.temp >= 90) {
            color = "is-danger";
        } else if (props.temp >= 75) {
            color = "is-warning";
        }

        return (
            <progress
            className={"progress " + color}
            value={props.level}
            max="100" />
        );
    }

    function HeatLabel (props) {
        return (
            <div>
                <p className="heading">{props.name}</p>
                <p className="title">{props.temp}&#8451;</p>
            </div>
        );
    }

    class SimpleLineChart extends React.Component {
        render () {

            const tickFormatter = (time) => {
                return new Date(time * 1e3).toISOString().slice(-13, -5);
            };

            return (
                <LineChart width={600} height={250} data={props.sensorValue.tempHistory}>
                   <XAxis dataKey="date" tickFormatter={tickFormatter} angle={-45} textAnchor="end" height={65}/>
                   <YAxis />
                   <CartesianGrid strokeDasharray="3 3"/>
                   <ReferenceLine y={props.sensorValue.setpoint} label="Måltemp." stroke="red" strokeDasharray="3 3" />
                   <Line type="monotone" dataKey="temp" stroke="#8884d8" isAnimationActive={false} dot={false}/>
              </LineChart>
            );
        }
    }


    return (
        <div className="has-text-centered">
            <div className="box">
                <HeatLabel name={props.sensorValue.name}
                           temp={props.sensorValue.temp} />
                <HeatGauge level={props.heater.level} />
                <HeatIcon active={props.heater.active} />
                <SimpleLineChart />
                <p className="heading">Måltemp: {props.sensorValue.setpoint}</p>
            </div>
        </div>
    );
}

class ControlPanel extends React.Component {
    constructor (props) {
        super(props);
        this.state = {
            "sensors": {},
            "heaters": {},
            "pumps": {},
            "coolers": {}
        };
    }

    getSensor(sensor_id) {
        if (sensor_id in this.state.sensors) {
            return this.state.sensors[sensor_id];
        } else {
            console.warn("Sensor id: '"+sensor_id+"' does not exist");
            return 0;
        }
    }

    getHeater(heater_id) {
        if (heater_id in this.state.heaters) {
            return this.state.heaters[heater_id];
        } else {
            console.warn("Heater id: '"+heater_id+"' does not exist");
            return 0;
        }
    }

    getPump(pump_id) {
        if (pump_id in this.state.pumps) {
            return this.state.pumps[pump_id];
        } else {
            console.warn("Pump id: '"+pump_id+"' does not exist");
            return 0;
        }
    }

    renderSensor(sensor_id) {
        return (<Sensor
                    heater={this.getHeater(sensor_id)}
                    sensorValue={this.getSensor(sensor_id)}
                    />)
    }

    renderPump(pump_id) {
        return (
                <Pump pump={this.getPump(pump_id)}
                      handleClick = {() => {
                          var pump = this.getPump(pump_id);
                          var newState = pump.active ? "off" : "on";

                          setPump(pump_id, newState);
                }}/>
        );
    }

    renderHeater(heater_id) {
        const stateCb = this.setState.bind(this);

        return (
                <Heater heater={this.getHeater(heater_id)}
                    handleEnableClick = {() => {
                        var heater = this.getHeater(heater_id);
                        setHeaterEnabledState(heater_id,
                                              !heater.enabled,
                                              stateCb
                        );
                    }}
                    handleActivateClick = {() => {
                        var heater = this.getHeater(heater_id);
                        setHeaterActiveState(heater_id, !heater.active, stateCb);
                    }}
                    setpointChanged = {(event) => {
                        var heater = this.getHeater(heater_id);
                        setHeaterSetpoint(heater_id, event.target.value, stateCb);
                    }}
                    handleAutomationStateChangeReq = {(new_state) => {
                        var sensor = this.getSensor(heater_id);
                        setSensorAutomationState(heater_id, new_state, stateCb);
                    }}
                    setpoint = {this.getSensor(heater_id).setpoint}
                    heating_stages = {this.getSensor(heater_id).heating_stages}
                />
        );
    }

    componentDidMount() {
        fetchState((response) => {this.setState(response.data)});

        setInterval(() => {
            fetchState((response) => {this.setState(response.data)});
        }, 5000);
    }

    render() {
        return (
            <div>
                <div className="tile is-ancestor">
                    <div className="tile is-vertical is-parent">
                        <div className="tile is-parent">
                            <div className="tile is-4 is-child">
                                {this.renderSensor("bk")}
                            </div>
                            <div className="tile is-4 is-child">
                                {this.renderSensor("hlt")}
                            </div>
                            <div className="tile is-4 is-child">
                                {this.renderSensor("mlt")}
                            </div>
                        </div>
                        <div className="tile is-parent">
                            <div className="tile is-4 is-child">
                                {this.renderPump("mlt")}
                            </div>
                        </div>
                        <div className="tile is-parent">
                            <div className="tile is-3 is-child">
                                {this.renderHeater("mlt")}
                            </div>
                            <div className="tile is-3 is-child">
                                {this.renderHeater("hlt")}
                            </div>
                            <div className="tile is-3 is-child">
                                {this.renderHeater("bk")}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

ReactDOM.render(
  <ControlPanel />,
  document.getElementById('root')
);

function fetchState(cb) {
    return axios.get("/state")
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
