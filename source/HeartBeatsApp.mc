import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Timer;
using Toybox.Sensor;
using Toybox.ActivityRecording;
using Toybox.FitContributor;

class HeartBeatsApp extends Application.AppBase {

    private var view as HeartBeatsView?;
    private var timer as Timer.Timer?;
    private var session;
    private var fit_field;
    private static const MAX_RECORDS = 5;

    function initialize() {
        AppBase.initialize();
    }

    // onStart() is called on application start up or a resume
    function onStart(state as Dictionary?) as Void 
    {
        start_session ();
    }

    // onStop() is called when your application is exiting or has to be suspended
    function onStop(state as Dictionary?) as Void 
    {
        stop_session ();
    }

    // Return the initial view of your application here
    function getInitialView() as Array<Views or InputDelegates>? 
    {
        view = new HeartBeatsView ();
        return [view] as Array<Views or InputDelegates>;
    }

    function start_session () as Void
    {
        if (session == null || !session.isRecording ()) 
        {
            session = ActivityRecording.createSession ({
                :name => "HeartBeats",
                :sport => Activity.SPORT_GENERIC,
                :subSport => Activity.SUB_SPORT_GENERIC
            });
            fit_field = session.createField (
                "Heart beat intervals", 0, FitContributor.DATA_TYPE_UINT16, { :count => MAX_RECORDS, :units => "ms" });
            Sensor.registerSensorDataListener (method (:handle_sensor_event), 
                { 
                    :period => 1, //second, up to 4
                    :accelerometer => { :enabled => false },
                    :heartBeatIntervals => { :enabled => true }
                });
            timer = new Timer.Timer ();
            timer.start (method (:handle_timer), 1000, true);
            session.start ();
       }
    }

    function stop_session () as Void
    {
        if (session != null && session.isRecording ()) 
        {
            Sensor.unregisterSensorDataListener ();
            timer.stop ();
            session.stop ();
            session.save ();
            session = null;
            fit_field = null;
            timer = null;
        }
    }

    // Note that an active session would log anyway each second (unless Smart Recording?)
    function handle_sensor_event (sensor_data as Sensor.SensorData) as Void
    {
        if (sensor_data.heartRateData == null)
        {
            return;
        }
        // Better to fail if over MAX_RECORDS
        var intervals = sensor_data.heartRateData.heartBeatIntervals;
        if (intervals.size () > 0)
        {
            fit_field.setData (intervals);
            view.records += intervals.size ();
        }
    }

    function handle_timer () as Void 
    {
        view.seconds += 1;
        WatchUi.requestUpdate ();
    }
}

function getApp() as HeartBeatsApp {
    return Application.getApp() as HeartBeatsApp;
}