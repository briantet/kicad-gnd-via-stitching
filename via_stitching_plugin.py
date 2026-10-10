"""
GND Via Stitching Plugin for KiCad 10  —  v1.3.0
Teters Technology LLC — teters.ai
"""

import pcbnew
import wx

LAYER_CHOICES = [
    ("Through (F.Cu ↔ B.Cu)", None),
    ("F.Cu only",              pcbnew.F_Cu),
    ("B.Cu only",              pcbnew.B_Cu),
]

PREVIEW_LAYER = pcbnew.User_1

class ViaStitchDialog(wx.Dialog):
    def __init__(self, parent, board):
        super().__init__(parent,
                         title="GND Via Stitching  •  Teters Technology",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                         size=(450, 560))
        self.board = board
        self._build_ui()

    def _build_ui(self):
        p  = wx.Panel(self)
        vs = wx.BoxSizer(wx.VERTICAL)

        def row(label, ctrl):
            h  = wx.BoxSizer(wx.HORIZONTAL)
            st = wx.StaticText(p, label=label, size=(210, -1))
            h.Add(st,   0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            h.Add(ctrl, 1, wx.EXPAND)
            vs.Add(h, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 12)

        self.t_spacing = wx.TextCtrl(p, value="2.5")
        self.t_drill   = wx.TextCtrl(p, value="0.4")
        self.t_pad     = wx.TextCtrl(p, value="0.8")
        self.t_clear   = wx.TextCtrl(p, value="0.35")
        row("Grid spacing (mm):",           self.t_spacing)
        row("Via drill diameter (mm):",     self.t_drill)
        row("Via pad diameter (mm):",       self.t_pad)
        row("Clearance from objects (mm):", self.t_clear)

            
        netinfo = self.board.GetNetInfo()
        net_names = []
        for name in netinfo.NetsByName().keys():
            s = str(name)
            if s:
                net_names.append(s)
        nets = sorted(net_names)
        self.c_net = wx.ComboBox(p, choices=nets, style=wx.CB_READONLY)
        default = "GND" if "GND" in nets else (nets[0] if nets else "")
        self.c_net.SetStringSelection(default)
        self.c_net.Bind(wx.EVT_COMBOBOX, self._on_net_change)
        row("Net:", self.c_net)

        self.c_layer = wx.Choice(p, choices=[l[0] for l in LAYER_CHOICES])
        self.c_layer.SetSelection(0)
        row("Via layer:", self.c_layer)

        self.zones = []
        self.c_zone = wx.Choice(p, choices=["— Full board outline —"])
        self.c_zone.SetSelection(0)
        row("Restrict to zone:", self.c_zone)

        self.cb_outline   = wx.CheckBox(p, label="Stay inside board edge outline")
        self.cb_courtyard = wx.CheckBox(p, label="Respect courtyard layers (stricter)")
        self.cb_outline.SetValue(True)
        self.cb_courtyard.SetValue(True)
        vs.Add(self.cb_outline,   0, wx.LEFT | wx.TOP, 12)
        vs.Add(self.cb_courtyard, 0, wx.LEFT | wx.TOP, 6)

        hb = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_preview = wx.Button(p, label="Preview")
        self.btn_place   = wx.Button(p, wx.ID_OK,     label="Place Vias")
        self.btn_cancel  = wx.Button(p, wx.ID_CANCEL, label="Cancel")
        self.btn_preview.Bind(wx.EVT_BUTTON, self._on_preview)
        hb.Add(self.btn_preview, 0, wx.RIGHT, 8)
        hb.Add(self.btn_place,   0, wx.RIGHT, 4)
        hb.Add(self.btn_cancel,  0)
        vs.Add(hb, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 14)

        self.lbl_status = wx.StaticText(p, label="")
        self.lbl_status.SetForegroundColour(wx.Colour(40, 140, 40))
        vs.Add(self.lbl_status, 0, wx.ALIGN_CENTER | wx.BOTTOM, 8)

        p.SetSizer(vs)

    def _on_net_change(self, _evt):
        pass

    def _on_preview(self, _evt):
        if hasattr(self, '_preview_cb'):
            self._preview_cb(self.get_params())

    def mm(self, ctrl):
        return float(ctrl.GetValue().replace(",", "."))

    def get_params(self):
        return dict(
            spacing    = self.mm(self.t_spacing),
            drill      = self.mm(self.t_drill),
            pad        = self.mm(self.t_pad),
            clearance  = self.mm(self.t_clear),
            net_name   = self.c_net.GetStringSelection(),
            layer_idx  = self.c_layer.GetSelection(),
            zone       = None,
            use_outline= self.cb_outline.GetValue(),
            courtyard  = self.cb_courtyard.GetValue(),
        )

    def set_status(self, msg):
        self.lbl_status.SetLabel(msg)
        self.Layout()


def _build_obstacles(board, clearance_nm, use_courtyard):
    obs = []

    def expand(bb, extra=0):
        return (bb.GetLeft() - extra, bb.GetTop() - extra,
                bb.GetRight() + extra, bb.GetBottom() + extra)

    for fp in board.GetFootprints():
        obs.append(expand(fp.GetBoundingBox(), clearance_nm))

    for track in board.GetTracks():
        if hasattr(track, 'GetDrillValue'):
            cx, cy = track.GetX(), track.GetY()
            r = track.GetWidth() // 2 + clearance_nm
            obs.append((cx-r, cy-r, cx+r, cy+r))
        else:
            tbb = track.GetBoundingBox()
            hw  = track.GetWidth() // 2 + clearance_nm
            obs.append((tbb.GetLeft()-hw, tbb.GetTop()-hw,
                        tbb.GetRight()+hw, tbb.GetBottom()+hw))
    return obs


def _board_contains(board, x, y):
    bb = board.GetBoardEdgesBoundingBox()
    return (bb.GetLeft() <= x <= bb.GetRight() and
            bb.GetTop()  <= y <= bb.GetBottom())


def _candidate_points(board, p):
    sp  = pcbnew.FromMM(p["spacing"])
    cl  = pcbnew.FromMM(p["clearance"])
    pad = pcbnew.FromMM(p["pad"])
    hp  = pad // 2 + cl

    bb = board.GetBoardEdgesBoundingBox()
    x_min, y_min = bb.GetLeft(),  bb.GetTop()
    x_max, y_max = bb.GetRight(), bb.GetBottom()

    obstacles = _build_obstacles(board, cl, p["courtyard"])

    def blocked(x, y):
        for (x1, y1, x2, y2) in obstacles:
            if x1-hp <= x <= x2+hp and y1-hp <= y <= y2+hp:
                return True
        return False

    def in_bounds(x, y):
        if p["use_outline"] and not _board_contains(board, x, y):
            return False
        return True

    y = y_min + sp // 2
    while y <= y_max:
        x = x_min + sp // 2
        while x <= x_max:
            if in_bounds(x, y) and not blocked(x, y):
                yield (x, y)
            x += sp
        y += sp


class PreviewManager:
    def __init__(self, board):
        self.board  = board
        self._items = []

    def show(self, points, pad_nm):
        self.clear()
        r = pad_nm // 2
        for (x, y) in points:
            circle = pcbnew.PCB_SHAPE(self.board)
            circle.SetShape(pcbnew.SHAPE_T_CIRCLE)
            circle.SetLayer(PREVIEW_LAYER)
            circle.SetStart(pcbnew.VECTOR2I(int(x), int(y)))
            circle.SetEnd(pcbnew.VECTOR2I(int(x + r), int(y)))
            circle.SetWidth(pcbnew.FromMM(0.05))
            self.board.Add(circle)
            self._items.append(circle)
        pcbnew.Refresh()
        return len(self._items)

    def clear(self):
        for item in self._items:
            try:
                self.board.Remove(item)
            except Exception:
                pass
        self._items = []
        pcbnew.Refresh()


class ViaStitchingPlugin(pcbnew.ActionPlugin):

    def defaults(self):
        self.name                = "GND Via Stitching"
        self.category            = "Modify PCB"
        self.description         = "Place GND vias on a neat grid avoiding traces and components."
        self.show_toolbar_button = True

    def Run(self):
        board   = pcbnew.GetBoard()
        preview = PreviewManager(board)
        dlg     = ViaStitchDialog(None, board)

        def do_preview(params):
            pts   = list(_candidate_points(board, params))
            count = preview.show(pts, pcbnew.FromMM(params["pad"]))
            dlg.set_status(f"Preview: {count} via(s) — click Place Vias to commit.")

        dlg._preview_cb = do_preview

        result = dlg.ShowModal()
        preview.clear()

        if result != wx.ID_OK:
            dlg.Destroy()
            return

        p   = dlg.get_params()
        dlg.Destroy()

        net = board.FindNet(p["net_name"])
        if net is None:
            wx.MessageBox(f"Net '{p['net_name']}' not found.",
                          "Error", wx.OK | wx.ICON_ERROR)
            return

        pad_nm       = pcbnew.FromMM(p["pad"])
        dr_nm        = pcbnew.FromMM(p["drill"])
        layer_choice = LAYER_CHOICES[p["layer_idx"]][1]

        placed = 0
        for (x, y) in _candidate_points(board, p):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
            via.SetWidth(pad_nm)
            via.SetDrill(dr_nm)
            via.SetNet(net)
            
            if layer_choice is not None:
                via.SetLayerPair(layer_choice, layer_choice)
            board.Add(via)
            placed += 1

        pcbnew.Refresh()
        wx.MessageBox(
            f"✓  Placed {placed} {p['net_name']} via(s)\n\n"
            f"   Grid:      {p['spacing']} mm\n"
            f"   Drill:     {p['drill']} mm\n"
            f"   Pad:       {p['pad']} mm\n"
            f"   Clearance: {p['clearance']} mm\n\n"
            "Run DRC to verify no violations.",
            "Via Stitching Complete",
            wx.OK | wx.ICON_INFORMATION
        )

ViaStitchingPlugin().register()