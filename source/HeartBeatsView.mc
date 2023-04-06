import Toybox.Graphics;
import Toybox.WatchUi;

class HeartBeatsView extends WatchUi.View 
{
    public var seconds;
    public var records;

    function initialize() {
        View.initialize();
    }

    // Load your resources here
    function onLayout(dc as Dc) as Void {
    }

    // Called when this View is brought to the foreground. Restore
    // the state of this View and prepare it to be shown. This includes
    // loading resources into memory.
    function onShow () as Void {
        seconds = 0;
        records = 0;
    }

    // Update the view
    function onUpdate (dc as Dc) as Void 
    {
        // Call the parent onUpdate function to redraw the layout
        View.onUpdate (dc);

        var font_height = dc.getFontHeight (Graphics.FONT_SMALL);
        var draw_x = dc.getWidth () >> 1;
        var draw_h = dc.getHeight () >> 1;

        dc.setColor (Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);

        draw_h -= font_height;
        var minutes = seconds / 60;
        var hours = minutes / 60;
        var sec = seconds % 60;
        //var str = Lang.format ("$1$:$2$:$3$", [hours, minutes, sec]);
        var str = hours.format ("%02d") + ":" + minutes.format ("%02d") + ":" + sec.format ("%02d");
        dc.drawText (draw_x, draw_h, Graphics.FONT_SMALL, str, Graphics.TEXT_JUSTIFY_CENTER);

        draw_h += font_height;
        dc.drawText (draw_x, draw_h, Graphics.FONT_SMALL, records, Graphics.TEXT_JUSTIFY_CENTER);
    }

    // Called when this View is removed from the screen. Save the
    // state of this View here. This includes freeing resources from
    // memory.
    function onHide() as Void {
    }

}
