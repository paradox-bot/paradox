cd tex
pdflatex $1.tex >> texout.log 2>&1
if [ $? != 0 ];
then
    grep -A 10 -m 1 "^!" $1.log;
else
    echo "";
fi
convert -background white -flatten -border 80 -density 500 -quality 300 -trim +repage -border 40 $1.pdf $1.png;


if [ "$2" = "transparent" ];
then
  convert $1.png -negate $1.png;
  convert $1.png -fuzz 40% -transparent black $1.png;
fi
if [ "$2" = "black" ];
then
  convert $1.png -negate $1.png;
  convert $1.png -fuzz 40% -fill black -opaque black $1.png;
fi
if [ "$2" = "grey" ];
then
  convert $1.png -negate $1.png;
  convert $1.png -fuzz 40% -fill 'rgb(54,57,63)' -opaque black $1.png;
fi
if [ "$2" = "default" ];
then
  convert $1.png -negate $1.png;
  convert $1.png -fuzz 40% -fill 'rgb(54,57,63)' -opaque black $1.png;
fi
if [ "$2" = "gray" ];
then
  convert $1.png -negate $1.png;
  convert $1.png -fuzz 40% -fill 'rgb(54,57,63)' -opaque black $1.png;
fi
if [ "$2" = "dark" ];
then
  convert $1.png -negate $1.png;
  convert $1.png -fuzz 40% -fill 'rgb(35,39,42)' -opaque black $1.png;
fi

height=`convert $1.png -format "%h" info:`
width=`convert $1.png -format "%[fx:w]" info:`
minwidth=1000
newwidth=$(( width > minwidth ? width : minwidth ))

convert -background transparent -extent ${newwidth}x${height} $1.png $1.png
#cd tex
#latex -no-shell-escape -halt-on-error $1.tex >> $1.texout.log 2>&1
#dvipng -bg White -T tight -D 620 -o $1.png $1
