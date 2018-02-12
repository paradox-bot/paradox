cd tex
pdflatex $1.tex
convert -background white -flatten -border 80 -density 500 -quality 100 $1.pdf $1.png

