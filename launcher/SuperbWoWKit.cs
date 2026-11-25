// Superb WoW Kit. One window that says whether the kit is installed and
// current, and installs or updates it by running install.ps1 from GitHub at
// the newest commit on main. Builds with the C# 5 compiler in every Windows.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Net;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

class Kit : Form {
	const string Repo = "jackisgolden/superb-wow-kit";
	static readonly Color Bg = Color.FromArgb(22, 24, 29), Fg = Color.FromArgb(232, 232, 236),
		Dim = Color.FromArgb(138, 143, 152), Green = Color.FromArgb(87, 200, 120),
		Amber = Color.FromArgb(232, 178, 64), Blue = Color.FromArgb(64, 128, 232);

	Label dot = new Label(), status = new Label(), detail = new Label();
	Button button = new Button();
	TextBox log = new TextBox();
	Timer poll = new Timer { Interval = 2000 };
	List<CheckBox> optional = new List<CheckBox>();
	string addons, latest;
	Action onClick = delegate { }, refresh = delegate { };

	[DllImport("user32.dll")] static extern bool SetProcessDPIAware();
	[DllImport("dwmapi.dll")] static extern int DwmSetWindowAttribute(IntPtr hwnd, int attribute, ref int value, int size);

	[STAThread]
	static void Main() {
		SetProcessDPIAware();
		ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
		Application.EnableVisualStyles();
		Application.Run(new Kit());
	}

	Kit() {
		SuspendLayout();
		AutoScaleDimensions = new SizeF(96, 96);
		AutoScaleMode = AutoScaleMode.Dpi;
		Text = "Superb WoW Kit";
		Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
		BackColor = Bg;
		ForeColor = Fg;
		Font = new Font("Segoe UI", 10);
		FormBorderStyle = FormBorderStyle.FixedSingle;
		MaximizeBox = false;
		StartPosition = FormStartPosition.CenterScreen;
		ClientSize = new Size(460, 124);

		var title = new Label { Text = "Superb WoW Kit", Font = new Font("Segoe UI Semibold", 15), Location = new Point(20, 16), AutoSize = true };
		dot.SetBounds(20, 60, 20, 24);
		dot.Text = "●";
		status.SetBounds(40, 60, 270, 24);
		status.Font = new Font("Segoe UI", 11);
		detail.SetBounds(22, 88, 290, 20);
		detail.Font = new Font("Segoe UI", 8.5f);
		detail.ForeColor = Dim;
		detail.AutoEllipsis = true;
		button.SetBounds(330, 64, 110, 36);
		button.FlatStyle = FlatStyle.Flat;
		button.FlatAppearance.BorderSize = 0;
		button.Cursor = Cursors.Hand;
		button.Click += delegate { onClick(); };
		log.SetBounds(20, 124, 420, 220);
		log.Multiline = true;
		log.ReadOnly = true;
		log.ScrollBars = ScrollBars.Vertical;
		log.BorderStyle = BorderStyle.None;
		log.BackColor = Color.FromArgb(14, 15, 18);
		log.ForeColor = Dim;
		log.Font = new Font("Consolas", 9);
		log.Visible = false;
		Controls.AddRange(new Control[] { title, dot, status, detail, button, log });
		ResumeLayout(false);

		poll.Tick += delegate { if (!WowRunning()) { poll.Stop(); Check(); } };
		HandleCreated += delegate { int dark = 1; DwmSetWindowAttribute(Handle, 20, ref dark, 4); };
		Shown += delegate { Check(); };
	}

	void Set(Color color, string text, string label, Action click, bool primary) {
		dot.ForeColor = color;
		status.Text = text;
		button.Text = label;
		button.Enabled = click != null;
		onClick = click ?? delegate { };
		button.BackColor = primary ? Blue : Color.FromArgb(44, 47, 54);
		button.ForeColor = primary && click != null ? Color.White : Fg;
	}

	async void Check() {
		addons = addons ?? FindAddOns();
		if (addons == null) {
			Set(Amber, "Can't find WoW Forever", "Pick folder", Pick, true);
			detail.Text = "Install it from Battle.net, or pick your World of Warcraft folder.";
			return;
		}
		detail.Text = addons;
		Set(Dim, "Checking for updates…", "Close", null, false);
		foreach (var box in optional) box.Enabled = false;
		latest = await Task.Run(() => LatestCommit());
		var rows = latest == null ? null : await Task.Run(() => OptionalRows(latest));
		if (rows == null) {
			Set(Amber, "Can't reach GitHub", "Retry", Check, false);
			return;
		}

		var stamp = Path.Combine(addons, @"!ForeverKit\Installed.lua");
		var installed = File.Exists(stamp)
			? Regex.Match(File.ReadAllText(stamp), "commit = \"(\\w+)\", date = \"([\\d-]+)\", folders = \"([^\"]*)\"")
			: Match.Empty;
		bool present = Directory.Exists(Path.Combine(addons, "!ForeverKit"));
		// The stamp lists the folders the kit installed, and only those count.
		bool missing = installed.Success && installed.Groups[3].Value.Split(',').Any(f => !Directory.Exists(Path.Combine(addons, f)));
		string verb = !present ? "Install" : missing ? "Repair" : "Update";

		var folders = installed.Success ? installed.Groups[3].Value.Split(',') : new string[0];
		ShowOptional(rows, folders);
		refresh = delegate { ShowState(installed, present, missing, verb); };
		refresh();
	}

	// Tag holds whether the kit has the addon, so a changed tick means work to do.
	void ShowOptional(List<string[]> rows, string[] folders) {
		var ticks = optional.ToDictionary(b => b.Text, b => b.Checked != (bool)b.Tag ? (bool?)b.Checked : null);
		foreach (var box in optional) { Controls.Remove(box); box.Dispose(); }
		optional.Clear();
		int line = LogicalToDevice(26), top = LogicalToDevice(114);
		foreach (var row in rows) {
			bool has = folders.Contains(row[1].Split(',')[0]);
			bool? tick;
			ticks.TryGetValue(row[0] + " (optional)", out tick);
			var box = new CheckBox { Text = row[0] + " (optional)", Tag = has, Checked = tick ?? has, AutoSize = true, ForeColor = Fg,
				Location = new Point(LogicalToDevice(22), top + optional.Count * line) };
			box.CheckedChanged += delegate { refresh(); };
			optional.Add(box);
			Controls.Add(box);
		}
		int bottom = top + optional.Count * line + LogicalToDevice(10);
		log.Top = bottom;
		ClientSize = new Size(ClientSize.Width, log.Visible ? log.Bottom + log.Left : bottom);
	}

	int LogicalToDevice(int pixels) {
		return (int)Math.Round(pixels * CurrentAutoScaleDimensions.Width / 96);
	}

	void ShowState(Match installed, bool present, bool missing, string verb) {
		poll.Stop();
		bool changed = present && optional.Any(b => b.Checked != (bool)b.Tag);
		if (changed && !missing && installed.Success && installed.Groups[1].Value == latest) verb = "Apply";
		if (!changed && installed.Success && installed.Groups[1].Value == latest && !missing)
			Set(Green, "Up to date · installed " + installed.Groups[2].Value, "Close", Close, false);
		else if (WowRunning()) {
			Set(Amber, "Close WoW to " + verb.ToLower(), verb, null, true);
			poll.Start();
		} else
			Set(present ? Amber : Dim, !present ? "Not installed" : verb == "Apply" ? "Optional addons changed" : missing ? "Kit addons are missing" : "Update available", verb, Install, true);
	}

	async void Install() {
		foreach (var box in optional) box.Enabled = false;
		log.Clear();
		log.Visible = true;
		ClientSize = new Size(ClientSize.Width, log.Bottom + log.Left);
		Set(Blue, "Installing…", "Working", null, true);
		string script = Path.Combine(Path.GetTempPath(), "superb-wow-kit.ps1");
		try {
			await Task.Run(() => Client().DownloadFile("https://raw.githubusercontent.com/" + Repo + "/" + latest + "/install.ps1", script));
		} catch (WebException e) {
			log.AppendText(e.Message + Environment.NewLine);
			Check();
			return;
		}
		var start = new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File \"" + script + "\"") {
			UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true,
		};
		start.EnvironmentVariables["WOW_KIT_ADDONS"] = addons;
		start.EnvironmentVariables["WOW_KIT_SHA"] = latest;
		var chosen = optional.Where(b => b.Checked).Select(b => b.Text.Replace(" (optional)", "")).ToArray();
		start.EnvironmentVariables["WOW_KIT_OPTIONAL"] = chosen.Length > 0 ? string.Join(",", chosen) : "none";
		var run = Process.Start(start);
		DataReceivedEventHandler show = (sender, e) => {
			if (!string.IsNullOrWhiteSpace(e.Data)) BeginInvoke((Action)(() => log.AppendText(e.Data + Environment.NewLine)));
		};
		run.OutputDataReceived += show;
		run.ErrorDataReceived += show;
		run.BeginOutputReadLine();
		run.BeginErrorReadLine();
		await Task.Run(() => run.WaitForExit());
		Check();
	}

	void Pick() {
		var picker = new FolderBrowserDialog { Description = "Pick your World of Warcraft folder" };
		if (picker.ShowDialog(this) == DialogResult.OK && Directory.Exists(Path.Combine(picker.SelectedPath, "_forever_")))
			addons = Path.Combine(picker.SelectedPath, @"_forever_\Interface\AddOns");
		Check();
	}

	static WebClient Client() {
		var client = new WebClient();
		client.Headers["User-Agent"] = "superb-wow-kit";
		return client;
	}

	static string LatestCommit() {
		try {
			var client = Client();
			client.Headers["Accept"] = "application/vnd.github.sha";
			return client.DownloadString("https://api.github.com/repos/" + Repo + "/commits/main").Trim();
		} catch (WebException) {
			return null;
		}
	}

	// The name and folders of each optional row in addons.tsv.
	static List<string[]> OptionalRows(string sha) {
		try {
			var lines = Client().DownloadString("https://raw.githubusercontent.com/" + Repo + "/" + sha + "/addons.tsv")
				.Split('\n').Select(l => l.TrimEnd('\r').Split('\t')).ToList();
			int name = Array.IndexOf(lines[0], "name"), folders = Array.IndexOf(lines[0], "folders"), flag = Array.IndexOf(lines[0], "optional");
			return lines.Skip(1).Where(l => flag >= 0 && l.Length > flag && l[flag] != "")
				.Select(l => new[] { l[name], l[folders] }).ToList();
		} catch (WebException) {
			return null;
		}
	}

	static bool WowRunning() {
		return Process.GetProcessesByName("Wow").Length > 0;
	}

	static string FindAddOns() {
		var bases = new List<string>();
		var reg = Registry.GetValue(@"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Blizzard Entertainment\World of Warcraft", "InstallPath", null) as string;
		if (reg != null) {
			reg = reg.TrimEnd('\\');
			bases.Add(Regex.IsMatch(Path.GetFileName(reg), "^_.+_$") ? Path.GetDirectoryName(reg) : reg);
		}
		foreach (var drive in DriveInfo.GetDrives())
			foreach (var sub in new[] { "Program Files (x86)", "Program Files", "Games", "" })
				bases.Add(Path.Combine(drive.Name, sub, "World of Warcraft"));
		var game = bases.Select(b => Path.Combine(b, "_forever_")).FirstOrDefault(Directory.Exists);
		return game == null ? null : Path.Combine(game, @"Interface\AddOns");
	}
}
