const {LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceLine} = Recharts;

class VesselControl extends React.Component {
    constructor (props) {
        super(props);

        this.state = {
            "active": false,
            "is_manual": false,
            "level": 0.0,
            "mode": "off",
            "pid": {"setpoint": {"temperature": 0}}
        };

        this.props.es.addEventListener("vessel-heater-" + props.id, e => {
            this.setState(JSON.parse(e.data))


            const field = this.setpointInputRef.current;
            field.value = this.state.pid.setpoint.temperature;
        });

        this.setpointInputRef = React.createRef();
    }

    componentDidMount() {
        const field = this.setpointInputRef.current;
        field.value = this.state.pid.setpoint.temperature;
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
            <LineChart width={760} height={255} data={this.state.chart}>
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
    }

    render() {
        const setpointChanged = (e) => {
            console.log(e)
        }

        return (
            <div className="has-text-centered">
                <div className="box">
                    <TemperatureLabel name={this.props.name} id={this.props.id} es={this.props.es}/>
                    <HeatGauge id={this.props.id} es={this.props.es}/>
                    <SimpleLineChart id={this.props.id} es={this.props.es}/>
                    <VesselControl setpointChanged={setpointChanged}
                                   id={this.props.id}
                                   es={this.props.es}/>
                </div>
            </div>
        );
    }
}

class GraphPanel extends React.Component {
    constructor (props) {
        super(props);
    }

    render() {
        return (
            <div>
            {
                this.props.vessels.map((vessel, i) => {
                    return (<Vessel name={vessel.name} id={vessel.id} key={vessel.id} es={this.props.es}/>)
                })
            }
            </div>
        );
    }
}

class Tabs extends React.Component {
    constructor (props) {
        super(props);

        this.state = {"vessels": []};

        this.eventSource = new EventSource("/v1/stream");

        fetchVessels((e) => {
            this.setState({"vessels": e.data})
        });

        this.tab_0 = React.createRef();
        this.tab_1 = React.createRef();

        this.onTabChange = (newTab) =>{
            switch (newTab) {
                case 0:
                    this.tab_0.current.className = "";
                    this.tab_1.current.className = "is-hidden";
                    break;
                case 1:
                    this.tab_0.current.className = "is-hidden";
                    this.tab_1.current.className = "";
                    break;
            }
        }
    }

    render () {
        return (
                <div>
                    <TabRow onTabChange={this.onTabChange}/>
                    <div ref={this.tab_0}>
                        <ControlPanel es={this.eventSource} vessels={this.state.vessels} />
                    </div>
                    <div ref={this.tab_1} className="is-hidden">
                        <GraphPanel vessels={this.state.vessels} es={this.eventSource} id="hlt" />
                    </div>
                </div>
        )
    }
}


class ControlPanel extends React.Component {
    constructor (props) {
        super(props);

        this.setpointChanged = (sp) => {
            console.log("New setpoint: " + sp);
        }
    }

    render () {
        console.log("Rendering ControlPanel");

        return (
            <div>
                {
                this.props.vessels.map((vessel, i) => {
                    console.log("Vessel: " + vessel.id);
                    <VesselControl setpointChanged={this.setpointChanged}
                                   id={vessel.id}
                                   es={this.props.es}/>
                })
                }
            </div>
        )
    }
}

function TabRow(props) {
    var tab_0 = React.createRef();
    var tab_1 = React.createRef();

    function tabChange(newIdx) {
        switch (newIdx) {
            case 0:
                tab_0.current.className = "is-active";
                tab_1.current.className = "";
                break;
            case 1:
                tab_0.current.className = "";
                tab_1.current.className = "is-active";
                break;
        }

        props.onTabChange(newIdx);
    }

    return (
    <div className="tabs is-centered is-boxed">
      <ul>
        <li ref={tab_0} className="is-active" onClick={() => tabChange(0)}>
          <a>
            <span className="icon is-small"><i className="fas fa-tachometer-alt" aria-hidden="true"></i></span>
            <span>Set temperatures</span>
          </a>
        </li>
        <li ref={tab_1} onClick={() => tabChange(1)}>
          <a>
            <span className="icon is-small"><i className="fas fa-chart-area" aria-hidden="true"></i></span>
            <span>Graphs</span>
          </a>
        </li>
      </ul>
    </div>
    );
}

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

ReactDOM.render(
    <Tabs />,
    document.getElementById('root')
);

