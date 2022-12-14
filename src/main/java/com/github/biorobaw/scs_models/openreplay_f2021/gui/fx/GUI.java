package com.github.biorobaw.scs_models.openreplay_f2021.gui.fx;


import com.github.biorobaw.scs.experiment.Experiment;
import com.github.biorobaw.scs.gui.Display;
import com.github.biorobaw.scs.gui.DrawPanel;
import com.github.biorobaw.scs.gui.displays.java_fx.drawer.universe.CycleDataDrawer;
import com.github.biorobaw.scs.gui.displays.java_fx.drawer.universe.FeederDrawer;
import com.github.biorobaw.scs.gui.displays.java_fx.drawer.universe.PathDrawer;
import com.github.biorobaw.scs.gui.displays.java_fx.drawer.universe.RobotDrawer;
import com.github.biorobaw.scs.gui.displays.java_fx.drawer.universe.WallDrawer;
import com.github.biorobaw.scs.utils.math.Doubles;
import com.github.biorobaw.scs.gui.displays.java_fx.drawer.plot.Plot;
import com.github.biorobaw.scs.gui.displays.java_fx.drawer.plot.RuntimesDrawer;
import com.github.biorobaw.scs_models.openreplay_f2021.gui.fx.drawers.*;
import com.github.biorobaw.scs_models.openreplay_f2021.model.ReplayModel;
import com.github.biorobaw.scs_models.openreplay_f2021.model.ReplayModelUnseen;

public class GUI {

	// =========== PARAMETERS =====================
	static final float   wall_thickness = 0.01f;
	static final float   highlighted_wall_thickness = wall_thickness * 5;

	// ============ VARIABLES =====================

	// reference to the display and model
	Display d = Experiment.get().display;
	ReplayModel model;

	// reference to drawers
	public WallDrawer wallDrawer;
	public PathDrawer pathDrawer;
	public RobotDrawer rDrawer;
	public FeederDrawer fDrawer;

	int numScales;
	public PCDrawer[] pcDrawers;
	public VDrawer[] TDrawers;
	public VDrawer[] VDrawers;
	public VScatterDrawer vscatterDrawer;
	public ReplayDrawer[] replayDrawers;


	public PolarDataDrawer probabilityDrawer;
	public PolarDataDrawer biasDrawer;

	public WallBiasHighlighterDrawer wallBiasDrawer;

	public Plot runtimes;


	final static String panel_pc = "PC Activation ";
	final static String panel_traces = "Traces ";
	final static String panel_value = "PC Value ";
	final static String panel_probabilities = "Probabilities";
	final static String panel_bias = "Biases";
	final static String panel_runtimes = "Run times";
	final static String panel_value_scatter = "Value vs PC radius";
	final static String panel_replay = "Replay Matrix";


	public GUI(ReplayModel model) {
		numScales = model.pcs.length;
		this.model = model;
		createPanels();
		createDrawers();
		addDrawersToPanels();

	}

	public GUI(ReplayModelUnseen model) {
		numScales = model.pcs.length;
		this.model = model;
		createPanels();
		createDrawers();
		addDrawersToPanels();

	}


	private void createPanels() {
		// =========== CREATE PANELS =================
		// PC PANELS
		int size = 300;
		for (int i = 0; i < numScales; i++) {
			d.addPanel(new DrawPanel(size, size), panel_pc + i, 0, i, 1, 1);
		}

		// REPLAY PANELS
		for (int i = 0; i < numScales; i++) {
			d.addPanel(new DrawPanel(size, size), panel_replay + i, 1, 2, 1, 1);
		}

		// TRACE PANELS
		for (int i = 0; i < numScales; i++) {
			d.addPanel(new DrawPanel(size, size), panel_traces + i, 1, i, 1, 1);
		}

		// VALUE PANELS
		for (int i = 0; i < numScales; i++) {
			d.addPanel(new DrawPanel(size, size), panel_value + i, 2, i, 1, 1);
		}

		// OBS: First 3 rows are reserved for
		// ACTION SELECTION PANELS
		d.addPanel(new DrawPanel(size,size), panel_bias, 0, numScales, 1, 1);
		d.addPanel(new DrawPanel(size,size), panel_probabilities, 0, numScales+1, 1, 1);

		d.addPanel(new DrawPanel(size,size), panel_runtimes, 1, numScales, 1, 1);
		d.addPanel(new DrawPanel(size,size), panel_value_scatter, 2, numScales, 1, 1);


	}

	private void createDrawers() {
		// =========== CREATE DRAWERS ===============


		// Maze related drawers
		wallDrawer = new WallDrawer( wall_thickness);

		pathDrawer = new PathDrawer(model.getRobot().getRobotProxy());
//		pathDrawer.setColor(path_color);

		rDrawer = new RobotDrawer(model.getRobot().getRobotProxy());

		fDrawer = new FeederDrawer(0.1f);


		// PC drawers
		pcDrawers = new PCDrawer[numScales];
		for (int i = 0; i < numScales; i++) {
			var pc_bin = model.pc_bins[i];
			var pcs = model.pcs[i];
			pcDrawers[i] = new PCDrawer(pcs.xs, pcs.ys, pcs.rs,
						 				() -> pc_bin.active_pcs.as,
						 				() -> pc_bin.active_pcs.ids);
		}

		// Trace drawers:
		TDrawers = new VDrawer[numScales];
		for (int i = 0; i < numScales; i++) {
			var t = model.vTraces[i];
			var pcs = model.pcs[i];
			TDrawers[i] = new VDrawer(pcs.xs, pcs.ys, t.traces[0]);
			TDrawers[i].setMinValue(0);
		}

		// V drawers
		VDrawers = new VDrawer[numScales];
		for (int i = 0; i < numScales; i++) {
			var pcs = model.pcs[i];
			VDrawers[i] = new VDrawer(pcs.xs, pcs.ys, model.vTable[i]);
			VDrawers[i].distanceOption = 1; // use pc radis to draw PCs
			VDrawers[i].setMinValue(0);
			VDrawers[i].setMaxValue(1.5f);
			VDrawers[i].fixed_range = true;
		}

		// Replay drawers
		replayDrawers = new ReplayDrawer[numScales];
		for (int i = 0; i < numScales; i++) {
			var pcs = model.pcs[i];
			var rmatrix = model.rmatrix;
			replayDrawers[i] = new ReplayDrawer(pcs.xs, pcs.ys, model.vTable[i]);
			replayDrawers[i].distanceOption = 1; // use pc radis to draw PCs
			replayDrawers[i].setMinValue(0);
			replayDrawers[i].setMaxValue(1.5f);
			replayDrawers[i].fixed_range = true;
		}

		// RL and action selection drawers
		var num_angles = model.numActions;
		var angles = Doubles.mul(Doubles.range(num_angles), 2*Math.PI / num_angles);

		probabilityDrawer = new PolarDataDrawer("Probabilities" );
		probabilityDrawer.addData("Q softmax", angles, () -> model.softmax);
		probabilityDrawer.addData("Final Policy", angles, ()->model.action_selection_probs);
		probabilityDrawer.addArrow( ()->model.chosenAction * 2*Math.PI/num_angles);

		biasDrawer = new PolarDataDrawer("Biases");
		biasDrawer.addData("Affordances", angles, ()->model.affordances.affordances);
		biasDrawer.addData("Motion", angles, ()->model.motionBias.getBias());
		biasDrawer.addData("Obstacle", angles, () -> model.obstacle_biases.biases);

		wallBiasDrawer = new WallBiasHighlighterDrawer(highlighted_wall_thickness, model);

		int numEpisodes = Integer.parseInt(Experiment.get().getGlobal("numEpisodes").toString());
		runtimes = new RuntimesDrawer(0, 0, numEpisodes, 800);
//		runtimes.doLines = false;

		vscatterDrawer = new VScatterDrawer(-0.1, 1.1,model.pcs, model.vTable);
	}

	public void addDrawersToPanels() {

		// ======== ADD DRAWERS TO PANELS ============

		// UNIVERSE PANEL
		d.addDrawer("universe", "pcs", pcDrawers[0] );
		d.addDrawer("universe", "value", VDrawers[0]);
		d.addDrawer("universe", "wall bias", wallBiasDrawer);
		d.addDrawer("universe", "maze", wallDrawer );
		d.addDrawer("universe", "feeders", fDrawer);
		d.addDrawer("universe", "path", pathDrawer);
		d.addDrawer("universe", "cycle info", new CycleDataDrawer());
		d.addDrawer("universe", "robot", rDrawer);

		// RUNTIMES
		d.addDrawer(panel_runtimes, "runtimes", runtimes);

		// PC PANELS
		for (int i = 0; i < numScales; i++) {
			d.addDrawer(panel_pc + i, "PC layer " + i, pcDrawers[i]);
			d.addDrawer(panel_pc + i, "maze", wallDrawer);
			d.addDrawer(panel_pc + i, "robot other", rDrawer);
		}

		// REPLAY PANELS
		for (int i = 0; i < numScales; i++) {
			d.addDrawer(panel_replay + i, "Replay layer " + i, replayDrawers[i]);
			d.addDrawer(panel_replay + i, "maze", wallDrawer);
			d.addDrawer(panel_replay + i, "robot other", rDrawer);
		}

		// TRACE PANELS:
		for (int i = 0; i < numScales; i++) {
			d.addDrawer(panel_traces + i, "T layer " + i, TDrawers[i]);
			d.addDrawer(panel_traces + i, "maze", wallDrawer);
			d.addDrawer(panel_traces + i, "robot other", rDrawer);
		}

		// VALUE PANELS:
		for (int i = 0; i < numScales; i++) {
			d.addDrawer(panel_value + i, "V layer " + i, VDrawers[i]);
			d.addDrawer(panel_value + i, "maze", wallDrawer);
			d.addDrawer(panel_value + i, "robot other", rDrawer);
		}


		// ACTION SELECTION PANELS:
		d.addDrawer(panel_probabilities, "pDrawer", probabilityDrawer);
		d.addDrawer(panel_bias, "biasDrawer", biasDrawer);
		d.addDrawer(panel_value_scatter, panel_value_scatter, vscatterDrawer);






	}


}
