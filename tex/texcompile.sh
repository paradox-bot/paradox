cd tex
pdflatex $1.tex >> texout.log 2>&1
convert -background white -flatten -border 80 -density 500 -quality 100 $1.pdf $1.png
