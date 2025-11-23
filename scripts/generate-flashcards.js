const fs = require('fs');
const path = require('path');

// Function to parse CSV file
function parseCSV(content) {
  const lines = content.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim());
  const data = [];
  
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim());
    const obj = {};
    headers.forEach((header, index) => {
      obj[header] = values[index] || '';
    });
    data.push(obj);
  }
  
  return data;
}

// Function to recursively find all CSV files
function findCSVFiles(dir, baseDir = dir) {
  let results = [];
  const files = fs.readdirSync(dir);
  
  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      results = results.concat(findCSVFiles(filePath, baseDir));
    } else if (path.extname(file) === '.csv') {
      results.push({
        fullPath: filePath,
        relativePath: path.relative(baseDir, filePath)
      });
    }
  }
  
  return results;
}

// Function to copy files from public directory to dist
function copyPublicFiles(publicDir, distDir) {
  if (!fs.existsSync(publicDir)) {
    return;
  }
  
  const files = fs.readdirSync(publicDir);
  
  files.forEach(file => {
    const srcPath = path.join(publicDir, file);
    const destPath = path.join(distDir, file);
    const stat = fs.statSync(srcPath);
    
    if (stat.isDirectory()) {
      if (!fs.existsSync(destPath)) {
        fs.mkdirSync(destPath, { recursive: true });
      }
      copyPublicFiles(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
      console.log(`Copied: ${file}`);
    }
  });
}

// Main function
function generateFlashcards() {
  const textsDir = path.join(__dirname, '../texts');
  const distDir = path.join(__dirname, '../dist');
  
  // Create dist directory if it doesn't exist
  if (!fs.existsSync(distDir)) {
    fs.mkdirSync(distDir, { recursive: true });
  }
  
  // Find all CSV files
  const csvFiles = findCSVFiles(textsDir);
  
  // Index to store metadata about all files
  const index = {
    generatedAt: new Date().toISOString(),
    files: []
  };
  
  // Process each CSV file
  csvFiles.forEach(({ fullPath, relativePath }) => {
    console.log(`Processing: ${relativePath}`);
    
    // Read and parse CSV
    const content = fs.readFileSync(fullPath, 'utf-8');
    const flashcards = parseCSV(content);
    
    // Create corresponding JSON file path
    const jsonRelativePath = relativePath.replace('.csv', '.json');
    const jsonFullPath = path.join(distDir, jsonRelativePath);
    
    // Create directory structure in dist
    const jsonDir = path.dirname(jsonFullPath);
    if (!fs.existsSync(jsonDir)) {
      fs.mkdirSync(jsonDir, { recursive: true });
    }
    
    // Write JSON file with flashcards
    fs.writeFileSync(jsonFullPath, JSON.stringify(flashcards, null, 2), 'utf-8');
    
    // Add to index
    index.files.push({
      source: relativePath,
      output: jsonRelativePath,
      cardCount: flashcards.length,
      book: path.dirname(relativePath)
    });
  });
  
  // Write index.json
  const indexPath = path.join(distDir, 'index.json');
  fs.writeFileSync(indexPath, JSON.stringify(index, null, 2), 'utf-8');
  
  // Copy public files to dist
  const publicDir = path.join(__dirname, '../public');
  console.log('\nCopying public files...');
  copyPublicFiles(publicDir, distDir);
  
  console.log(`\nGeneration complete!`);
  console.log(`Processed ${csvFiles.length} files`);
  console.log(`Total flashcards: ${index.files.reduce((sum, f) => sum + f.cardCount, 0)}`);
  console.log(`Output directory: ${distDir}`);
}

// Run the script
try {
  generateFlashcards();
} catch (error) {
  console.error('Error generating flashcards:', error);
  process.exit(1);
}
