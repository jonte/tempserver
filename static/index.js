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

class SimpleLineChart extends React.Component {
    constructor (props) {
        super(props);
        this.state = {"chart": []};
    }

    componentDidMount() {
        this.eventSource = new EventSource("/v1/vessel/"+this.props.id+"/chart_stream");
        this.eventSource.onmessage = e => {
            this.setState({"chart": this.state.chart.concat(JSON.parse(e.data))})
        }
    }

    render () {
        const tickFormatter = (time) => {
            return new Date(time * 1e3).toISOString().slice(-13, -5);
        };

        let temp = (t) => {return t.temperature.temperature};
        let sp = (t) => {return t.setpoint.temperature};
        let heater_level = (t) => {return t.heater_level.power};

        return (
            <LineChart width={600} height={250} data={this.state.chart}>
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
        this.state = {"output": 0};
    }

    componentDidMount() {
//        this.eventSource = new EventSource("/v1/vessel/"+this.props.id+"/PID_stream");
//        this.eventSource.onmessage = e => {
//            this.setState({"output": JSON.parse(e.data).output})
//        }
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
            "unit": "C",
        };
    }

    componentDidMount() {
        this.eventSource = new EventSource("/v1/vessel/"+this.props.id+"/temperature_stream");
        this.eventSource.onmessage = e => {
            console.log("Event from " + this.props.name)
            this.setState(JSON.parse(e.data));
        }
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
        this.state = props.vessel;
    }

    render() {
        return (
            <div className="has-text-centered">
                <div className="box">
                    <TemperatureLabel name={this.state.name} id={this.state.id}/>
                    <HeatGauge id={this.state.id}/>
                    <SimpleLineChart id={this.state.id} />
                    <p className="heading">Måltemp: {this.state.pid_state.setpoint.temperature}°{this.state.pid_state.setpoint.unit}</p>
                </div>
            </div>
        );
    }
}

class ControlPanel extends React.Component {
    constructor (props) {
        super(props);
        this.state = {
            "vessels": [],
        };
    }

    getPump(pump_id) {
        if (pump_id in this.state.pumps) {
            return this.state.pumps[pump_id];
        } else {
            console.warn("Pump id: '"+pump_id+"' does not exist");
            return 0;
        }
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
                        var sensor = this.getVessel(heater_id);
                        setSensorAutomationState(heater_id, new_state, stateCb);
                    }}
                    setpoint = {this.getVessel(heater_id).setpoint}
                    heating_stages = {this.getVessel(heater_id).heating_stages}
                />
        );
    }

    updateVessels(vessels) {
        this.setState({"vessels": vessels});
    }

    componentDidMount() {
        fetchVessels((response) => {this.updateVessels(response.data)});
    }

    render() {
        return (
            <div>
                {
                    this.state.vessels.map((vessel, i) => {
                        return <Vessel key={i} vessel={vessel}/>
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
