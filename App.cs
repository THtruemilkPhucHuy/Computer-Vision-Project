
using System;
using System.IO;
using System.Linq;
using System.Drawing;
using System.Diagnostics;
using System.Globalization;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Web.Script.Serialization;

namespace WildfireIntelligence
{
    public class AppForm : Form
    {
        // =========================================
        // CONFIGURATION
        // =========================================

        private string projectRoot = "";
        private string pythonPath = "";
        private string modelPath = "";

        private readonly List<AnalysisResult> results =
            new List<AnalysisResult>();

        private readonly List<string> imageFiles =
            new List<string>();

        private DataGridView grid;
        private PictureBox preview;

        private Label lblTotal;
        private Label lblFire;
        private Label lblNeutral;
        private Label lblSmoke;
        private Label lblStatus;
        private Label lblSelected;
        private Label lblConfidence;
        private Label lblProbabilities;

        private ProgressBar progressBar;
        private ComboBox cmbWorkers;

        private Button btnImages;
        private Button btnFolder;
        private Button btnAnalyze;
        private Button btnExport;
        private Button btnProject;

        private bool isAnalyzing = false;

        private const string Marker = "WILDFIRE_JSON:";

        private readonly Color BackgroundColor =
            Color.FromArgb(15, 23, 42);

        private readonly Color PanelColor =
            Color.FromArgb(30, 41, 59);

        private readonly Color AccentColor =
            Color.FromArgb(249, 115, 22);

        private readonly Color TextColor =
            Color.FromArgb(241, 245, 249);

        // =========================================
        // RESULT MODEL
        // =========================================

        private class AnalysisResult
        {
            public string ImagePath { get; set; }

            public string FileName { get; set; }

            public string Label { get; set; }

            public double Confidence { get; set; }

            public Dictionary<string, double> Probabilities
                { get; set; }

            public string Status { get; set; }

            public string Error { get; set; }
        }

        // =========================================
        // CONSTRUCTOR
        // =========================================

        public AppForm()
        {
            Text = "Wildfire Intelligence";
            Size = new Size(1450, 900);
            MinimumSize = new Size(1100, 700);

            StartPosition = FormStartPosition.CenterScreen;

            BackColor = BackgroundColor;
            ForeColor = TextColor;

            Font = new Font("Segoe UI", 9F);

            DiscoverProjectRoot();
            BuildInterface();
            UpdateStatistics();
        }

        // =========================================
        // DISCOVER PROJECT ROOT
        // =========================================

        private void DiscoverProjectRoot()
        {
            string current = AppDomain.CurrentDomain.BaseDirectory;

            while (!string.IsNullOrEmpty(current))
            {
                bool hasPredict =
                    File.Exists(Path.Combine(current, "predict.py"));

                bool hasCheckpoint =
                    File.Exists(Path.Combine(
                        current,
                        "checkpoints",
                        "best_model.pth"
                    ));

                if (hasPredict && hasCheckpoint)
                {
                    projectRoot = current;
                    break;
                }

                DirectoryInfo parent =
                    Directory.GetParent(current);

                if (parent == null)
                    break;

                current = parent.FullName;
            }

            if (string.IsNullOrEmpty(projectRoot))
                projectRoot = AppDomain.CurrentDomain.BaseDirectory;

            pythonPath = Path.Combine(
                projectRoot,
                ".venv",
                "Scripts",
                "python.exe"
            );

            modelPath = Path.Combine(
                projectRoot,
                "checkpoints",
                "best_model.pth"
            );

            if (!File.Exists(pythonPath))
                pythonPath = "python";
        }

        // =========================================
        // UI HELPERS
        // =========================================

        private Label CreateLabel(
            string text,
            int size,
            FontStyle style = FontStyle.Regular)
        {
            return new Label
            {
                Text = text,
                ForeColor = TextColor,
                Font = new Font("Segoe UI", size, style),
                AutoSize = true
            };
        }

        private Button CreateButton(
            string text,
            Color color)
        {
            Button button = new Button();

            button.Text = text;
            button.Size = new Size(150, 42);

            button.FlatStyle = FlatStyle.Flat;
            button.FlatAppearance.BorderSize = 0;

            button.BackColor = color;
            button.ForeColor = Color.White;

            button.Font = new Font(
                "Segoe UI",
                9F,
                FontStyle.Bold
            );

            button.Cursor = Cursors.Hand;

            return button;
        }

        private Panel CreatePanel()
        {
            return new Panel
            {
                BackColor = PanelColor,
                Margin = new Padding(8),
                Padding = new Padding(14)
            };
        }

        // =========================================
        // BUILD INTERFACE
        // =========================================

        private void BuildInterface()
        {
            TableLayoutPanel root = new TableLayoutPanel();

            root.Dock = DockStyle.Fill;
            root.ColumnCount = 2;
            root.RowCount = 1;

            root.ColumnStyles.Add(
                new ColumnStyle(SizeType.Absolute, 230)
            );

            root.ColumnStyles.Add(
                new ColumnStyle(SizeType.Percent, 100)
            );

            Controls.Add(root);

            BuildSidebar(root);
            BuildMainDashboard(root);
        }

        // =========================================
        // SIDEBAR
        // =========================================

        private void BuildSidebar(TableLayoutPanel root)
        {
            Panel sidebar = new Panel();

            sidebar.Dock = DockStyle.Fill;
            sidebar.BackColor = Color.FromArgb(10, 16, 30);

            root.Controls.Add(sidebar, 0, 0);

            Label logo = CreateLabel(
                "🔥 WILDFIRE",
                17,
                FontStyle.Bold
            );

            logo.ForeColor = AccentColor;
            logo.Location = new Point(20, 28);

            sidebar.Controls.Add(logo);

            Label subtitle = CreateLabel(
                "INTELLIGENCE SYSTEM",
                8,
                FontStyle.Bold
            );

            subtitle.ForeColor = Color.Silver;
            subtitle.Location = new Point(22, 58);

            sidebar.Controls.Add(subtitle);

            Label menu = CreateLabel(
                "OVERVIEW\n\n" +
                "IMAGE ANALYSIS\n\n" +
                "BATCH PROCESSING\n\n" +
                "MODEL CONFIGURATION\n\n" +
                "REPORTS",
                10,
                FontStyle.Bold
            );

            menu.ForeColor = Color.FromArgb(180, 190, 210);
            menu.Location = new Point(22, 125);
            menu.Size = new Size(195, 240);

            sidebar.Controls.Add(menu);

            Label modelStatus = CreateLabel(
                "MODEL STATUS",
                10,
                FontStyle.Bold
            );

            modelStatus.Location = new Point(22, 430);

            sidebar.Controls.Add(modelStatus);

            Label modelInfo = CreateLabel(
                File.Exists(modelPath)
                    ? "● MODEL AVAILABLE"
                    : "● MODEL NOT FOUND",
                9,
                FontStyle.Bold
            );

            modelInfo.ForeColor =
                File.Exists(modelPath)
                    ? Color.LightGreen
                    : Color.OrangeRed;

            modelInfo.Location = new Point(22, 460);

            sidebar.Controls.Add(modelInfo);

            Label version = CreateLabel(
                "WILDFIRE INTELLIGENCE\nVersion 1.0.0",
                8
            );

            version.ForeColor = Color.Gray;
            version.Location = new Point(22, 790);

            sidebar.Controls.Add(version);
        }

        // =========================================
        // MAIN DASHBOARD
        // =========================================

        private void BuildMainDashboard(TableLayoutPanel root)
        {
            Panel main = new Panel();

            main.Dock = DockStyle.Fill;
            main.BackColor = BackgroundColor;
            main.Padding = new Padding(18);

            root.Controls.Add(main, 1, 0);

            TableLayoutPanel layout = new TableLayoutPanel();

            layout.Dock = DockStyle.Fill;
            layout.ColumnCount = 1;
            layout.RowCount = 5;

            layout.RowStyles.Add(
                new RowStyle(SizeType.Absolute, 80)
            );

            layout.RowStyles.Add(
                new RowStyle(SizeType.Absolute, 125)
            );

            layout.RowStyles.Add(
                new RowStyle(SizeType.Absolute, 105)
            );

            layout.RowStyles.Add(
                new RowStyle(SizeType.Percent, 100)
            );

            layout.RowStyles.Add(
                new RowStyle(SizeType.Absolute, 145)
            );

            main.Controls.Add(layout);

            BuildHeader(layout);
            BuildControls(layout);
            BuildStatistics(layout);
            BuildResults(layout);
            BuildPreview(layout);
        }

        // =========================================
        // HEADER
        // =========================================

        private void BuildHeader(TableLayoutPanel layout)
        {
            Panel header = new Panel();
            header.Dock = DockStyle.Fill;

            Label title = CreateLabel(
                "Wildfire Intelligence",
                23,
                FontStyle.Bold
            );

            title.Location = new Point(8, 5);

            header.Controls.Add(title);

            Label description = CreateLabel(
                "AI-powered Fire / Neutral / Smoke classification",
                9
            );

            description.ForeColor = Color.Silver;
            description.Location = new Point(10, 42);

            header.Controls.Add(description);

            layout.Controls.Add(header, 0, 0);
        }

        // =========================================
        // CONTROLS
        // =========================================

        private void BuildControls(TableLayoutPanel layout)
        {
            Panel panel = CreatePanel();
            panel.Dock = DockStyle.Fill;

            Label heading = CreateLabel(
                "IMAGE UPLOAD & ANALYSIS",
                11,
                FontStyle.Bold
            );

            heading.Location = new Point(14, 10);
            panel.Controls.Add(heading);

            btnImages = CreateButton(
                "+ Add Images",
                Color.FromArgb(51, 65, 85)
            );

            btnImages.Location = new Point(15, 50);
            btnImages.Click += AddImages;

            panel.Controls.Add(btnImages);

            btnFolder = CreateButton(
                "+ Add Folder",
                Color.FromArgb(51, 65, 85)
            );

            btnFolder.Location = new Point(175, 50);
            btnFolder.Click += AddFolder;

            panel.Controls.Add(btnFolder);

            btnProject = CreateButton(
                "Browse Project",
                Color.FromArgb(51, 65, 85)
            );

            btnProject.Location = new Point(335, 50);
            btnProject.Click += BrowseProject;

            panel.Controls.Add(btnProject);

            cmbWorkers = new ComboBox();

            cmbWorkers.Items.AddRange(
                new object[] { "1", "2", "3", "4" }
            );

            cmbWorkers.SelectedIndex = 0;
            cmbWorkers.DropDownStyle =
                ComboBoxStyle.DropDownList;

            cmbWorkers.Location = new Point(510, 58);
            cmbWorkers.Width = 70;

            panel.Controls.Add(cmbWorkers);

            Label workersLabel = CreateLabel("Workers", 9);
            workersLabel.Location = new Point(510, 32);

            panel.Controls.Add(workersLabel);

            btnAnalyze = CreateButton(
                "▶ START ANALYSIS",
                AccentColor
            );

            btnAnalyze.Size = new Size(180, 42);
            btnAnalyze.Location = new Point(610, 50);

            btnAnalyze.Click += async (s, e) =>
                await StartAnalysis();

            panel.Controls.Add(btnAnalyze);

            lblSelected = CreateLabel(
                "0 images selected",
                9
            );

            lblSelected.ForeColor = Color.LightGray;
            lblSelected.Location = new Point(15, 100);

            panel.Controls.Add(lblSelected);

            layout.Controls.Add(panel, 0, 1);
        }

        // =========================================
        // STATISTICS
        // =========================================

        private void BuildStatistics(TableLayoutPanel layout)
        {
            FlowLayoutPanel stats = new FlowLayoutPanel();

            stats.Dock = DockStyle.Fill;
            stats.WrapContents = false;

            lblTotal = CreateLabel("0", 22, FontStyle.Bold);
            lblFire = CreateLabel("0", 22, FontStyle.Bold);
            lblNeutral = CreateLabel("0", 22, FontStyle.Bold);
            lblSmoke = CreateLabel("0", 22, FontStyle.Bold);

            stats.Controls.Add(
                CreateStatCard("TOTAL IMAGES", lblTotal)
            );

            stats.Controls.Add(
                CreateStatCard("FIRE DETECTED", lblFire)
            );

            stats.Controls.Add(
                CreateStatCard("NEUTRAL", lblNeutral)
            );

            stats.Controls.Add(
                CreateStatCard("SMOKE DETECTED", lblSmoke)
            );

            layout.Controls.Add(stats, 0, 2);
        }

        private Panel CreateStatCard(
            string title,
            Label value)
        {
            Panel card = CreatePanel();

            card.Size = new Size(185, 85);

            Label heading = CreateLabel(
                title,
                8,
                FontStyle.Bold
            );

            heading.ForeColor = Color.Silver;
            heading.Location = new Point(10, 8);

            value.Location = new Point(10, 32);

            card.Controls.Add(heading);
            card.Controls.Add(value);

            return card;
        }

        // =========================================
        // RESULTS TABLE
        // =========================================

        private void BuildResults(TableLayoutPanel layout)
        {
            Panel panel = CreatePanel();
            panel.Dock = DockStyle.Fill;

            Label heading = CreateLabel(
                "BATCH ANALYSIS RESULTS",
                11,
                FontStyle.Bold
            );

            heading.Dock = DockStyle.Top;
            heading.Height = 30;

            panel.Controls.Add(heading);

            grid = new DataGridView();

            grid.Dock = DockStyle.Fill;

            grid.BackgroundColor = PanelColor;
            grid.BorderStyle = BorderStyle.None;

            grid.AllowUserToAddRows = false;
            grid.AllowUserToDeleteRows = false;

            grid.ReadOnly = true;
            grid.MultiSelect = false;

            grid.SelectionMode =
                DataGridViewSelectionMode.FullRowSelect;

            grid.AutoSizeColumnsMode =
                DataGridViewAutoSizeColumnsMode.Fill;

            grid.RowHeadersVisible = false;

            grid.EnableHeadersVisualStyles = false;

            grid.ColumnHeadersDefaultCellStyle.BackColor =
                Color.FromArgb(15, 23, 42);

            grid.ColumnHeadersDefaultCellStyle.ForeColor =
                Color.White;

            grid.DefaultCellStyle.BackColor = PanelColor;
            grid.DefaultCellStyle.ForeColor = Color.White;

            grid.DefaultCellStyle.SelectionBackColor =
                Color.FromArgb(51, 65, 85);

            grid.DefaultCellStyle.SelectionForeColor =
                Color.White;

            grid.Columns.Add("File", "IMAGE");
            grid.Columns.Add("Class", "PREDICTION");
            grid.Columns.Add("Confidence", "CONFIDENCE");
            grid.Columns.Add("Status", "STATUS");

            grid.Columns["File"].FillWeight = 180;
            grid.Columns["Class"].FillWeight = 90;
            grid.Columns["Confidence"].FillWeight = 80;
            grid.Columns["Status"].FillWeight = 80;

            grid.SelectionChanged += GridSelectionChanged;

            panel.Controls.Add(grid);

            layout.Controls.Add(panel, 0, 3);
        }

        // =========================================
        // PREVIEW AND PROBABILITIES
        // =========================================

        private void BuildPreview(TableLayoutPanel layout)
        {
            Panel panel = CreatePanel();
            panel.Dock = DockStyle.Fill;

            preview = new PictureBox();

            preview.Location = new Point(15, 12);
            preview.Size = new Size(125, 110);

            preview.SizeMode = PictureBoxSizeMode.Zoom;
            preview.BackColor = Color.FromArgb(15, 23, 42);

            panel.Controls.Add(preview);

            lblStatus = CreateLabel(
                "System ready",
                10,
                FontStyle.Bold
            );

            lblStatus.Location = new Point(160, 12);
            panel.Controls.Add(lblStatus);

            lblConfidence = CreateLabel(
                "Confidence: -",
                10,
                FontStyle.Bold
            );

            lblConfidence.Location = new Point(160, 42);
            panel.Controls.Add(lblConfidence);

            lblProbabilities = CreateLabel(
                "Fire: - | Neutral: - | Smoke: -",
                9
            );

            lblProbabilities.Location = new Point(160, 72);
            panel.Controls.Add(lblProbabilities);

            progressBar = new ProgressBar();

            progressBar.Location = new Point(160, 100);
            progressBar.Size = new Size(500, 18);

            progressBar.Minimum = 0;
            progressBar.Maximum = 100;

            panel.Controls.Add(progressBar);

            btnExport = CreateButton(
                "EXPORT CSV",
                Color.FromArgb(22, 163, 74)
            );

            btnExport.Location = new Point(690, 50);
            btnExport.Click += ExportCsv;

            panel.Controls.Add(btnExport);

            layout.Controls.Add(panel, 0, 4);
        }

        // =========================================
        // ADD IMAGES
        // =========================================

        private void AddImages(object sender, EventArgs e)
        {
            using (OpenFileDialog dialog = new OpenFileDialog())
            {
                dialog.Title = "Select wildfire images";

                dialog.Filter =
                    "Image files|*.jpg;*.jpeg;*.png;*.bmp;*.webp;*.tif;*.tiff";

                dialog.Multiselect = true;

                if (dialog.ShowDialog() == DialogResult.OK)
                    AddFiles(dialog.FileNames);
            }
        }

        // =========================================
        // ADD FOLDER
        // =========================================

        private void AddFolder(object sender, EventArgs e)
        {
            using (FolderBrowserDialog dialog =
                new FolderBrowserDialog())
            {
                dialog.Description =
                    "Select folder containing images";

                if (dialog.ShowDialog() == DialogResult.OK)
                {
                    try
                    {
                        string[] files = Directory
                            .GetFiles(
                                dialog.SelectedPath,
                                "*.*",
                                SearchOption.AllDirectories
                            )
                            .Where(IsImage)
                            .ToArray();

                        AddFiles(files);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show(
                            ex.Message,
                            "Folder error",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error
                        );
                    }
                }
            }
        }

        private bool IsImage(string path)
        {
            string ext = Path.GetExtension(path).ToLowerInvariant();

            return ext == ".jpg" ||
                   ext == ".jpeg" ||
                   ext == ".png" ||
                   ext == ".bmp" ||
                   ext == ".webp" ||
                   ext == ".tif" ||
                   ext == ".tiff";
        }

        private void AddFiles(IEnumerable<string> files)
        {
            foreach (string file in files)
            {
                string fullPath = Path.GetFullPath(file);

                if (!imageFiles.Contains(
                    fullPath,
                    StringComparer.OrdinalIgnoreCase))
                {
                    imageFiles.Add(fullPath);

                    grid.Rows.Add(
                        Path.GetFileName(fullPath),
                        "Pending",
                        "-",
                        "Waiting"
                    );
                }
            }

            lblSelected.Text =
                imageFiles.Count + " images selected";

            UpdateStatistics();
        }

        // =========================================
        // PROJECT CONFIGURATION
        // =========================================

        private void BrowseProject(object sender, EventArgs e)
        {
            using (FolderBrowserDialog dialog =
                new FolderBrowserDialog())
            {
                dialog.Description =
                    "Select Wildfire Python project folder";

                if (dialog.ShowDialog() != DialogResult.OK)
                    return;

                string root = dialog.SelectedPath;

                string predict = Path.Combine(root, "predict.py");

                string checkpoint = Path.Combine(
                    root,
                    "checkpoints",
                    "best_model.pth"
                );

                if (!File.Exists(predict) ||
                    !File.Exists(checkpoint))
                {
                    MessageBox.Show(
                        "Folder must contain predict.py and " +
                        "checkpoints\\best_model.pth",
                        "Invalid project folder"
                    );

                    return;
                }

                projectRoot = root;

                modelPath = checkpoint;

                string venvPython = Path.Combine(
                    root,
                    ".venv",
                    "Scripts",
                    "python.exe"
                );

                if (File.Exists(venvPython))
                    pythonPath = venvPython;

                lblStatus.Text = "Project configured";
            }
        }

        // =========================================
        // START BATCH ANALYSIS
        // =========================================

        private async Task StartAnalysis()
        {
            if (isAnalyzing)
                return;

            if (imageFiles.Count == 0)
            {
                MessageBox.Show("Please add images first.");
                return;
            }

            if (!File.Exists(Path.Combine(projectRoot, "predict.py")) ||
                !File.Exists(modelPath))
            {
                MessageBox.Show(
                    "Cannot find predict.py or model checkpoint.",
                    "Configuration error"
                );

                return;
            }

            if (pythonPath != "python" &&
                !File.Exists(pythonPath))
            {
                MessageBox.Show(
                    "Python executable not found."
                );

                return;
            }

            isAnalyzing = true;

            btnAnalyze.Enabled = false;
            btnImages.Enabled = false;
            btnFolder.Enabled = false;

            progressBar.Value = 0;
            progressBar.Maximum = imageFiles.Count;

            lblStatus.Text = "Analysis running...";

            results.Clear();

            foreach (DataGridViewRow row in grid.Rows)
            {
                row.Cells["Class"].Value = "Pending";
                row.Cells["Confidence"].Value = "-";
                row.Cells["Status"].Value = "Waiting";
            }

            int workers = Convert.ToInt32(
                cmbWorkers.SelectedItem
            );

            SemaphoreSlim semaphore =
                new SemaphoreSlim(workers);

            int completed = 0;

            try
            {
                var tasks = imageFiles.Select(async path =>
                {
                    await semaphore.WaitAsync();

                    try
                    {
                        AnalysisResult result =
                            await Task.Run(() => RunPrediction(path));

                        Interlocked.Increment(ref completed);

                        this.BeginInvoke(new Action(() =>
                        {
                            results.Add(result);

                            UpdateGridResult(result);

                            progressBar.Value =
                                Math.Min(completed, progressBar.Maximum);

                            lblStatus.Text =
                                "Analyzed " + completed +
                                " / " + imageFiles.Count;

                            UpdateStatistics();
                        }));
                    }
                    finally
                    {
                        semaphore.Release();
                    }
                }).ToArray();

                await Task.WhenAll(tasks);

                UpdateStatistics();

                lblStatus.Text = "Analysis completed";

                MessageBox.Show(
                    "Analysis completed successfully.",
                    "Wildfire Intelligence",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    ex.ToString(),
                    "Analysis error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
            finally
            {
                semaphore.Dispose();

                isAnalyzing = false;

                btnAnalyze.Enabled = true;
                btnImages.Enabled = true;
                btnFolder.Enabled = true;
            }
        }

        // =========================================
        // PYTHON INFERENCE
        // =========================================

        private AnalysisResult RunPrediction(string imagePath)
        {
            AnalysisResult result = new AnalysisResult
            {
                ImagePath = imagePath,
                FileName = Path.GetFileName(imagePath),
                Label = "Error",
                Confidence = 0,
                Status = "Failed",
                Probabilities = new Dictionary<string, double>()
            };

            try
            {
                // Python bridge:
                // import predict
                // predict.predict(image, checkpoint)

                string pythonCode =
                    "import sys,json; " +
                    "from predict import predict; " +
                    "label,confidence,probs=predict(sys.argv[1],sys.argv[2]); " +
                    "print('" + Marker + "'+json.dumps({" +
                    "'label':str(label)," +
                    "'confidence':float(confidence)," +
                    "'probs':{str(k):float(v) for k,v in probs.items()}" +
                    "}))";

                ProcessStartInfo start =
                    new ProcessStartInfo();

                start.FileName = pythonPath;

                start.Arguments =
                    "-u -c " + QuoteArgument(pythonCode) +
                    " " + QuoteArgument(imagePath) +
                    " " + QuoteArgument(modelPath);

                start.WorkingDirectory = projectRoot;

                start.UseShellExecute = false;
                start.CreateNoWindow = true;

                start.RedirectStandardOutput = true;
                start.RedirectStandardError = true;

                using (Process process = new Process())
                {
                    process.StartInfo = start;

                    process.Start();

                    Task<string> outputTask =
                        process.StandardOutput.ReadToEndAsync();

                    Task<string> errorTask =
                        process.StandardError.ReadToEndAsync();

                    process.WaitForExit();

                    string output = outputTask.Result;
                    string error = errorTask.Result;

                    if (process.ExitCode != 0)
                    {
                        throw new Exception(
                            string.IsNullOrWhiteSpace(error)
                                ? output
                                : error
                        );
                    }

                    string jsonLine = output
                        .Split(new[] { "\r\n", "\n" },
                            StringSplitOptions.RemoveEmptyEntries)
                        .LastOrDefault(x =>
                            x.StartsWith(Marker));

                    if (jsonLine == null)
                    {
                        throw new Exception(
                            "Python did not return valid prediction JSON.\n" +
                            output + "\n" + error
                        );
                    }

                    string json =
                        jsonLine.Substring(Marker.Length);

                    JavaScriptSerializer serializer =
                        new JavaScriptSerializer();

                    var data =
                        serializer.Deserialize<Dictionary<string, object>>(
                            json
                        );

                    result.Label =
                        Convert.ToString(data["label"]);

                    result.Confidence =
                        Convert.ToDouble(
                            data["confidence"],
                            CultureInfo.InvariantCulture
                        );

                    var probabilityData =
                        data["probs"] as Dictionary<string, object>;

                    if (probabilityData != null)
                    {
                        foreach (var item in probabilityData)
                        {
                            result.Probabilities[item.Key] =
                                Convert.ToDouble(
                                    item.Value,
                                    CultureInfo.InvariantCulture
                                );
                        }
                    }

                    result.Status = "Success";
                }
            }
            catch (Exception ex)
            {
                result.Error = ex.Message;
                result.Status = "Failed";
            }

            return result;
        }

        // =========================================
        // WINDOWS ARGUMENT QUOTING
        // =========================================

        private string QuoteArgument(string value)
        {
            string escaped = value.Replace(
                "\\",
                "\\\\"
            );

            escaped = escaped.Replace(
                "\"",
                "\\\""
            );

            return "\"" + escaped + "\"";
        }

        // =========================================
        // UPDATE GRID
        // =========================================

        private void UpdateGridResult(AnalysisResult result)
        {
            foreach (DataGridViewRow row in grid.Rows)
            {
                if (string.Equals(
                    Convert.ToString(row.Cells["File"].Value),
                    result.FileName,
                    StringComparison.OrdinalIgnoreCase))
                {
                    // Match by full path via imageFiles index
                    // when duplicate file names exist.
                    string rowPath = null;

                    int rowIndex = row.Index;

                    if (rowIndex >= 0 &&
                        rowIndex < imageFiles.Count)
                    {
                        rowPath = imageFiles[rowIndex];
                    }

                    if (!string.Equals(
                        rowPath,
                        result.ImagePath,
                        StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    row.Cells["Class"].Value =
                        result.Status == "Success"
                            ? result.Label
                            : "Error";

                    row.Cells["Confidence"].Value =
                        result.Status == "Success"
                            ? result.Confidence.ToString("P2")
                            : "-";

                    row.Cells["Status"].Value =
                        result.Status;

                    row.Tag = result;

                    if (result.Status == "Success")
                    {
                        string label =
                            result.Label.ToLowerInvariant();

                        if (label.Contains("fire"))
                            row.Cells["Class"].Style.ForeColor =
                                Color.OrangeRed;

                        else if (label.Contains("smoke"))
                            row.Cells["Class"].Style.ForeColor =
                                Color.Gold;

                        else if (label.Contains("neutral"))
                            row.Cells["Class"].Style.ForeColor =
                                Color.LightGreen;
                    }

                    break;
                }
            }
        }

        // =========================================
        // PREVIEW SELECTED IMAGE
        // =========================================

        private void GridSelectionChanged(
            object sender,
            EventArgs e)
        {
            if (grid.CurrentRow == null)
                return;

            AnalysisResult result =
                grid.CurrentRow.Tag as AnalysisResult;

            if (result == null)
            {
                lblConfidence.Text = "Confidence: -";

                lblProbabilities.Text =
                    "Fire: - | Neutral: - | Smoke: -";

                return;
            }

            try
            {
                using (Image original =
                    Image.FromFile(result.ImagePath))
                {
                    Image old = preview.Image;

                    preview.Image = new Bitmap(original);

                    if (old != null)
                        old.Dispose();
                }
            }
            catch
            {
                preview.Image = null;
            }

            lblConfidence.Text =
                "Confidence: " +
                result.Confidence.ToString("P2");

            lblStatus.Text =
                result.Label + " | " + result.Status;

            if (result.Status == "Success")
            {
                lblProbabilities.Text = string.Join(
                    " | ",
                    result.Probabilities.Select(
                        x => x.Key + ": " + x.Value.ToString("P2")
                    )
                );
            }
            else
            {
                lblProbabilities.Text =
                    "Error: " + result.Error;
            }
        }

        // =========================================
        // UPDATE STATISTICS
        // =========================================

        private void UpdateStatistics()
        {
            lblTotal.Text = imageFiles.Count.ToString();

            lblFire.Text = results.Count(x =>
                x.Status == "Success" &&
                x.Label.IndexOf(
                    "fire",
                    StringComparison.OrdinalIgnoreCase
                ) >= 0
            ).ToString();

            lblSmoke.Text = results.Count(x =>
                x.Status == "Success" &&
                x.Label.IndexOf(
                    "smoke",
                    StringComparison.OrdinalIgnoreCase
                ) >= 0
            ).ToString();

            lblNeutral.Text = results.Count(x =>
                x.Status == "Success" &&
                x.Label.IndexOf(
                    "neutral",
                    StringComparison.OrdinalIgnoreCase
                ) >= 0
            ).ToString();
        }

        // =========================================
        // EXPORT CSV
        // =========================================

        private void ExportCsv(object sender, EventArgs e)
        {
            if (results.Count == 0)
            {
                MessageBox.Show("No results to export.");
                return;
            }

            using (SaveFileDialog dialog =
                new SaveFileDialog())
            {
                dialog.Filter = "CSV files|*.csv";

                dialog.FileName =
                    "Wildfire_Analysis_" +
                    DateTime.Now.ToString("yyyyMMdd_HHmmss") +
                    ".csv";

                if (dialog.ShowDialog() != DialogResult.OK)
                    return;

                try
                {
                    using (StreamWriter writer =
                        new StreamWriter(
                            dialog.FileName,
                            false,
                            System.Text.Encoding.UTF8))
                    {
                        writer.WriteLine(
                            "Image,Prediction,Confidence,Fire,Neutral,Smoke,Status,Error"
                        );

                        foreach (AnalysisResult r in results)
                        {
                            double fire = GetProbability(r, "Fire");
                            double neutral = GetProbability(r, "Neutral");
                            double smoke = GetProbability(r, "Smoke");

                            writer.WriteLine(string.Join(",",
                                Csv(r.FileName),
                                Csv(r.Label),
                                Csv(r.Confidence.ToString(
                                    "P2",
                                    CultureInfo.InvariantCulture)),
                                Csv(fire.ToString(
                                    "P2",
                                    CultureInfo.InvariantCulture)),
                                Csv(neutral.ToString(
                                    "P2",
                                    CultureInfo.InvariantCulture)),
                                Csv(smoke.ToString(
                                    "P2",
                                    CultureInfo.InvariantCulture)),
                                Csv(r.Status),
                                Csv(r.Error)
                            ));
                        }
                    }

                    MessageBox.Show(
                        "CSV exported successfully.",
                        "Export complete"
                    );
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        ex.Message,
                        "Export error"
                    );
                }
            }
        }

        private double GetProbability(
            AnalysisResult result,
            string className)
        {
            if (result.Probabilities == null)
                return 0;

            var item = result.Probabilities.FirstOrDefault(
                x => string.Equals(
                    x.Key,
                    className,
                    StringComparison.OrdinalIgnoreCase
                )
            );

            return item.Value;
        }

        private string Csv(string value)
        {
            if (value == null)
                value = "";

            return "\"" + value.Replace("\"", "\"\"") + "\"";
        }

        // =========================================
        // CLEANUP
        // =========================================

        protected override void OnFormClosed(
            FormClosedEventArgs e)
        {
            if (preview.Image != null)
            {
                preview.Image.Dispose();
                preview.Image = null;
            }

            base.OnFormClosed(e);
        }
    }
}
