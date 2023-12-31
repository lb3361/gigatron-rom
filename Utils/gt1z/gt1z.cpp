/* -*- C++ -*- */

#if __cplusplus < 201103L
# ifndef _MSC_VER
#   error "Please enable c++11 (e.g. -std=c++11)" __cplusplus
# endif
#endif

#include <cstdarg>
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <cstdint>
#include <cassert>
#include <cerrno>

#include <string>
#include <vector>
#include <fstream>
#include <algorithm>
#include <map>

using std::int16_t;

int relocatable = 0;

/* ========================================
 * UTILS
 */

int verbose = 0;

template<int level> void
info(const char *fmt, ...)
{
  if (verbose >= level) {
    std::va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "gt1z: %s: ", (level) ? "info" : "warning");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
  }
}

void
error(const char *fmt, ...)
{
  std::va_list ap;
  va_start(ap, fmt);
  fprintf(stderr,"gt1z: error: ");
  vfprintf(stderr, fmt, ap);
  fprintf(stderr, "\n");
  va_end(ap);
  std::exit(10);
}

template <typename T> int
unique(std::vector<T> &v)
{
  std::map<T,int> mm;     // not the fastest choice
  for(const auto &x : v)
    mm[x] = -1;
  int n = 0;
  for(auto &p : mm)
    p.second = n++;
  for(auto &x : v)
    x = mm[x];
  return n;
}

std::string ssprintf(const char *fmt, ...)
{
  std::string r;
  std::va_list ap;
  va_start(ap, fmt);
  int len = std::vsnprintf(nullptr, 0, fmt, ap);
  va_end(ap);
  if (len > 0)
    {
      r.resize(len);
      va_start(ap, fmt);
      std::vsnprintf(&r[0], len+1, fmt, ap);
      va_end(ap);
    }
  return r;
}

template <typename T>
std::string hex(std::vector<T> v, int max=6)
{
  std::string r;
  for(int i=0; i<v.size(); i++)
    if (i == max && v.size() > max + max) {
      i = v.size() - max;
      r += "...";
    } else
      r += ssprintf("%02x", v[i]);
  return r;
}

int minus(int addr, int offset)
{
  /* Subtract 16 bits numbers without borrow across bytes */
  return ((addr - offset) & 0xff)
    + (((addr & 0xff00) - (offset & 0xff00)) & 0xff00);
}



/* ========================================
 * GMEM
 */

class GMem
{
public:
  GMem();
  void load(std::string filename, bool strip=true);
  void save(std::string filename);
  void segment();
  void tokenize(int maxk = 256);
  bool operator==(const GMem &other) const
     { return exec == other.exec && ram == other.ram; }
  bool operator!=(const GMem &other) const
     { return ! operator==(other); }
public:
  int exec;
  std::vector<int16_t> ram;
  /* segments */
  std::vector<std::pair<int,int> > segments;
  /* tokenization */
  std::vector<int> rank;
  std::vector<int> firstpos;
  std::vector<int> nextpos;
};

GMem::GMem()
  : exec(-1)
{
  ram.resize(65536);
  for(int i=0; i<ram.size(); i++)
    ram[i] = -1;
}

void
GMem::load(std::string filename, bool strip)
{
  unsigned char buffer[256];
  std::ifstream f(filename, std::ios_base::in | std::ios_base::binary);
  if (! f.good())
    error("cannot open '%s' for reading", filename.c_str());
  f.read((char*)buffer, 3);
  while(f.good())
    {
      int addr = buffer[0] * 256 + buffer[1];
      int len = buffer[2];
      len = (len) ? len : 256;
      if (buffer[1] + len > 256)
        error("corrupted data in file '%s'", filename.c_str());
      f.read((char*)buffer, len);
      for (int i=0; i<len ; i++)
        ram[addr + i] = buffer[i];
      f.read((char*)buffer, 3);
      if (! buffer[0])
        break;
    }
  if (! f.good())
    error("error reading file '%s': %s", filename.c_str(), strerror(errno));
  exec = buffer[1] * 256 + buffer[2];
  if (f.peek() != EOF)
    info<0>("excess bytes found in file '%s'", filename.c_str());
  // removing ROMv1 patch
  if (strip && (exec & 0xfff0) == 0x5b80 && ram[exec] == 0x11 &&
      ram[exec+3] == 0x2b && ram[exec+4] == 0x1a && ram[exec+5] == 0xff)
    {
      int i = exec;
      info<0>("removing ROMv1 loader patch from %s at 0x%04x", filename.c_str(), i);
      exec = ram[exec+1] + 256 * ram[exec+2];
      for (int j=0; j<6; j++)
        ram[i+j] = -1;
    }
  info<2>("exec address %#04x", exec);
}

void
GMem::save(std::string filename)
{
  std::ofstream f(filename, std::ios_base::out | std::ios_base::binary);
  if (! f.good())
    error("cannot open '%s' for writing", filename.c_str());
  if (segments.empty())
    segment();
  unsigned char buffer[256];
  for (const auto &p : segments) {
    int addr = p.first;
    int l = p.second;
    buffer[0] = (addr >> 8) & 0xff;
    buffer[1] = addr & 0xff;
    buffer[2] = l & 0xff;
    f.write((char*)buffer, 3);
    for (int i=0; i < l; i++)
      buffer[i] = ram[addr + i];
    f.write((char*)buffer, l);
  }
  buffer[0] = 0;
  buffer[1] = (exec >> 8) & 0xff;
  buffer[2] = exec & 0xff;
  f.write((char*)buffer, 3);
  if (! f.good())
    error("error writing file '%s': %s", filename.c_str(), strerror(errno));
}

void
GMem::segment()
{
  segments.clear();
  for (int ah = 0; ah < 65536; ah += 256)
    {
      int al = 0;
      while (al < 256)
        {
          while (ram[ah+al] == -1 && al < 256)
            al++;
          int s = al;
          if (al < 256)
            {
              while(ram[ah+al] != -1 && al < 256)
                al++;
              segments.push_back(std::make_pair(ah+s, al-s));
            }
        }
    }
  if (verbose >= 3)
    for(const auto &v : segments)
      info<2>("segment (%#04x,%d)", v.first, v.second);
}

void
GMem::tokenize(int maxk)
{
  if (segments.empty())
    segment();
  /* Compute consecutive IDs for each suffix, segment-limited with
     maximal length (1<<maxk) sorted in lexicographic order. The zero
     ID is reserved for empty bytes (outside the segments). */
  rank.resize(ram.size());
  for (int i = 0; i < ram.size(); i++)
    rank[i] = ram[i];
  int n = unique(rank);
  int k = 1;
  while (k < maxk)
    {
      info<2>("tokenize #%d: %d unique IDs", k, n);
      for(const auto &p : segments)
        {
          int addr = p.first;
          int l = p.second;
          for(int i=0; i<l; i++)
            rank[addr + i] = rank[addr + i] * n
              + ((i + k < l) ? rank[addr + i + k] : 0);
        }
      n = unique(rank);
      k += k;
    }
  info<2>("tokenize #%d (final): %d unique IDs", k, n);
  /* Compute linked appearance lists for each ID */
  firstpos.resize(n);
  nextpos.resize(ram.size());
  for (int i = 0; i < n; i++)
    firstpos[i] = -1;
  for (int i = 0; i < ram.size(); i++)
    {
      int r = rank[i];
      nextpos[i] = firstpos[r];
      firstpos[r] = i;
    }
}




/* ========================================
 * COMPRESS
 */


struct Outputter
{
  std::ofstream f;
  int addr;
  int segaddr;
  int offset;
  std::vector<unsigned char> lits;
  int written;
  int predicted;

  Outputter(std::string filename)
    : addr(-1), segaddr(-1), offset(1), written(2), predicted(-1)
  {
    static char buffer[] = {0, -1};
    f.open(filename, std::ios_base::out | std::ios_base::binary);
    f.write(buffer, 2);
    if (! f.good())
      error("Cannot open file '%s' for writing", filename.c_str());
  }

  void write(const unsigned char *buffer, int n)
  {
    f.write((const char*)buffer, n);
    if (! f.good())
      error("error writing gt1z file: %s", strerror(errno));
    written += n;
  }

  void literal(int lcnt, const int16_t *b)
  {
    for (int i = 0; i < lcnt; i++)
      lits.push_back(b[i]);
    addr = (addr & 0xff00) + ((addr + lcnt) & 0xff); // low byte only
  }

  void match(int mcnt, int off)
  {
    unsigned char buffer[8];
    int nlits = lits.size();
    int token = (nlits < 7) ? (nlits << 4) : (0x7 << 4);
    assert(mcnt == 0 || mcnt >= 2);
    assert(mcnt == 0 || off >= 0);
    if (off != offset)
      token |= 0x80;
    if (mcnt > 0)
      offset = off;
    if (mcnt >= 2)
      token |= (mcnt - 1 < 15) ? (mcnt - 1) : 15;
    unsigned char *b = buffer;
    *b++ = token;
    if ((token & 0x70) == 0x70)
      *b++ = nlits;
    info<2>("  T=%02x L%d:'%s' %c%d:%#04x -(%d,%d)",
            token, nlits, hex(lits).c_str(), "DM"[token>>7],
            mcnt, minus(addr,offset), (offset>>8), (offset&0xff));
    write(buffer, b - buffer);
    if (nlits)
      write(lits.data(), nlits);
    lits.clear();
    b = buffer;
    if ((token & 0xf) == 0xf)
      *b++ = mcnt;
    if (mcnt > 0 && (token & 0x80))
      {
        int ohi = (offset >> 8) & 0xff;
        int olo = (offset - 1) & 0xff;
        int t = addr - segaddr;
        t = (t <= 0x7f) ? t : 0x7f;
        if (ohi == 0 && olo < t ||
            ohi == 1 && olo >= (t | 0x80))
          {
            *b++ = olo | 0x80;
          }
        else
          {
            assert((ohi & 0x80) == 0);
            *b++ = ohi;
            *b++ = offset;
          }
      }
    if (b > buffer)
      write(buffer, b - buffer);
    addr = (addr & 0xff00) + ((addr + mcnt) & 0xff);
  }

  void segment(int adr, int execlo = -1)
  {
    unsigned char buffer[8];
    unsigned char *b = buffer;
    bool longseg = true;
    if (segaddr >= 0)
      {
        longseg = (execlo >= 0) || (adr - segaddr != 256);
        if (longseg && execlo < 0)
          relocatable = 0;
        match(0, (longseg) ? offset : -1);
        if (predicted >= 0)
          if (verbose >= 3 || written != predicted)
            info<2>("  written %d predicted %d", written, predicted);
      }
    if (longseg)
      {
        *b++ = adr >> 8;
        *b++ = adr;
      }
    assert(execlo < 0 || !(adr & 0xff00));
    if (execlo >= 0)
      *b++ = execlo;            // just for finish()
    else
      addr = segaddr = adr;
    if (execlo >= 0)
      info<2>("-- EXEC 0x%02x%02x", adr, execlo);
    else
      info<2>("-- 0x%04x", addr);
    write(buffer, b - buffer);
  }

  void finish(int exec)
  {
    assert(addr >= 0);
    segment((exec >> 8) & 0xff, exec & 0xff);
    info<1>("written %d bytes", written);
  }

};


struct Chart
{
  const GMem &mem;
  int addr;
  int l;
  int bestc;
  std::vector<int> c, p, m, n;

  Chart(const GMem &mem, int addr, int l, int offset=1)
    : mem(mem), addr(addr), l(l), bestc(1000000000)
  {
    c.resize(l+1);
    p.resize(l+1);
    m.resize(l+1);
    n.resize(l+1);
    for (int i=0; i <= l; i++)
      {
        c[i] = bestc;
        p[i] = m[i] = n[i] = -1;
      }
    c[0] = 1;
    p[0] = 0;
    m[0] = n[0] = offset;
  }

  template<int strict=1>
  void add(int i, int j, int cost, int off = -1, int ofx = -1)
  {
    cost += c[i];
    if (cost + strict <= c[j])
      {
        c[j] = cost;
        p[j] = i;
        m[j] = off;
        n[j] = ofx;
        if (j == l)
          bestc = cost;
      }
  }

  void add_literal(int i)
  {
    int pi = i;
    while (n[pi] < 0)
      pi = p[pi];
    int nlits = i - pi + 1;
    int cost = nlits;
    if (nlits >= 7)
      cost++;
    add<0>(pi, i+1, cost);
  }

  void add_match(int i, int off)
  {
    int madr = minus(addr + i, off);
    const int16_t *base = &mem.ram[addr + i];
    const int16_t *match = &mem.ram[madr];
    int maxj = std::min(l - i, (madr | 0xff) + 1 - madr);
    int cost = 0;
    int s = i;
    while (m[s] < 0)
      s = p[s];
    if (m[s] != off)
      {
        int ohi = (off >> 8) & 0xff;
        int olo = (off - 1) & 0xff;
        int t = (i <= 0x7f) ? i : 0x7f;
        if (ohi == 0 && olo <= t ||
            ohi == 1 && olo > (t | 0x80))
          cost += 1;
        else
          cost += 2;                // not a direct match
      }
    int last = 0;               // <0 for lits, >=0 for matches
    for(int j = 0; j < maxj && cost <= bestc; j++)
      {
        if (last < 0) {
          if (base[j] == match[j])
            if (j + 1 < maxj && base[j+1] == match[j+1])
              last = j;
        } else if (base[j] != match[j]) {
          cost++;               // token
          last = -j;
        }
        if (last >= 0) {
          if (j - last == 15)
            cost++;
          add(i, i+j+1, cost+1, off, off);
        } else {
          cost++;
          if (j + last == 6)
            cost++;
          add(i, i+j+1, cost, off, -1);
        }
#ifndef BRUTISH
        if (c[i] + cost > c[i+j+1] + 2)
          break;              // SHORTCUT to save time.
#endif
      }
  }

  void output(const GMem& mem, Outputter &f)
  {
    /* reverse dynamic programming path */
    for (int i = l; i > 0; i = p[i])
      n[p[i]] = i;
    for (int i = 0; i < l; i = n[i])
      {
        int ni = n[i];
        int off = m[ni];
        if (off < 0)
          {
            // literal run
            f.literal(ni - i, &mem.ram[addr + i]);
          }
        else
          {
            // match + (lits + direct)*
            int madr = minus(addr + i, off);
            const int16_t *base = &mem.ram[addr];
            const int16_t *match = &mem.ram[madr - i];
            int j = i;
            while (j < ni) {
              int s = j;
              while (s < ni && base[s] == match[s])
                s++;
              if (s - j >= 2) {
                f.match(s - j, off);
                j = s;
              } else {
                f.literal(1, &base[j]);
                j++;
              }
            }
          }
      }
  }
};

int
compress(std::string fin, std::string fout)
{
  info<1>("compress('%s','%s')", fin.c_str(), fout.c_str());

  GMem mem;
  mem.load(fin);
  mem.segment();
  mem.tokenize(2);  // catalog all two-byte sequences

  Outputter f(fout);
  for (const auto &p : mem.segments)
    {
      int addr = p.first;
      int l = p.second;
      Chart chart(mem, addr, l, f.offset);
      f.segment(addr);
      for (int i = 0; i < l; i++)
        {
          chart.add_literal(i);
          int madr = mem.nextpos[addr+i];
          while (madr >= 0) {
            // try all matches of length >= 2
            int off = minus(addr + i, madr);
            if (off & 0x8000)
              break;
            chart.add_match(i, off);
            madr = mem.nextpos[madr];
          }
        }
      f.predicted = f.written + chart.c[l];
      chart.output(mem, f);
    }
  f.finish(mem.exec);
  return 0;
}


/* ========================================
 * DECOMPRESS
 */

int
decompress(std::string fin, std::string fout, bool verify)
{
  info<1>("decompress('%s','%s',%d)", fin.c_str(), fout.c_str(), (verify)?1:0);

  unsigned char buffer[8];
  std::vector<unsigned char> lits;
  GMem mem;
  std::ifstream f(fin, std::ios_base::in | std::ios_base::binary);
  if (! f.good())
    error("cannot open '%s' for reading", fin.c_str());
  // Magic number 0x00 0xff
  f.read((char*)buffer, 2);
  if (! (buffer[0] == 0 && buffer[1] == 255))
    error("invalid magic number in file '%s'", fin.c_str());
  // Read first seg
  f.read((char*)buffer, 2);
  int addr = buffer[0] * 256 + buffer[1];
  int segaddr = addr;
  int offset = 1;
  info<2>("-- 0x%04x", addr);
  while(f.good())
    {
      // Read token DLLLMMMM
      f.read((char*)buffer, 1);
      int token = buffer[0];
      int nlits = (token >> 4) & 7;  // number of literals
      if (nlits == 7) {
        f.read((char*)buffer, 1);    // overflow byte
        nlits = buffer[0];
        if (nlits == 0)
          nlits = 256;
      }
      if (nlits > 0) {
        lits.resize(nlits);
        f.read((char*)&lits[0], nlits);
        for (int i=0; i<nlits; i++)
          mem.ram[addr+i] = lits[i];
        addr = (addr & 0xff00) + ((addr + nlits) & 0xff);
      }
      int mcnt = token & 0xf;        // match  count
      if (mcnt == 15) {
        f.read((char*)buffer, 1);    // overflow byte
        mcnt = buffer[0];
        if (mcnt == 0)
          mcnt = 256;
      } else if (mcnt != 0) {
        mcnt += 1;                   // adjust count
      }
      if (mcnt > 0) {
        if (token & 0x80) {
          f.read((char*)buffer, 1); // offset
          if (buffer[0] & 0x80) {
            int t = addr - segaddr;
            t = (t <= 0x7f) ? t | 0x80 : 0xff;
            if (buffer[0] < t)
              offset = (buffer[0] + 1) & 0x7f;
            else
              offset = 256 + ((buffer[0] + 1) & 0xff);
          } else {
            f.read((char*)buffer+1, 1);
            offset = buffer[0] * 256 + buffer[1];
          }
        }
        int madr = minus(addr, offset);
        for (int i=0; i < mcnt; i++)
          mem.ram[addr+i] = mem.ram[madr+i];
      }
      info<2>("  T=%02x L%d:'%s' %c%d:%#04x -(%d,%d)",
              token, nlits, hex(lits).c_str(), "DM"[token>>7],
              mcnt, minus(addr,offset), (offset>>8), (offset&0xff));
      lits.clear();
      addr = (addr & 0xff00) + ((addr + mcnt) & 0xff); // low byte only
      if (mcnt == 0) {
        if (token & 0x80) {
          addr = segaddr = segaddr + 256;
        } else {
          f.read((char*)buffer, 2);  // end of segment (long)
          if (!buffer[0])            // end of file
            break;
          addr = segaddr = buffer[0] * 256 + buffer[1];
          relocatable = 0;
        }
        info<2>("-- 0x%04x", addr);
      }
    }
  f.read((char*)buffer+2, 1);
  mem.exec = buffer[1] * 256 + buffer[2];
  info<2>("-- EXEC 0x%04x", mem.exec);
  if (! f.good())
    error("error reading file '%s': %s", fin.c_str(), strerror(errno));
  if (f.peek() != EOF)
    info<0>("excess bytes found in file '%s'", fin.c_str());

  // Now save or verify
  if (verify)
    {
      GMem ref;
      ref.load(fout);
      if (mem != ref)
        error("decompressing '%s' does not match '%s'", fin.c_str(), fout.c_str());
      else
        info<1>("decompressing '%s' matches '%s'", fin.c_str(), fout.c_str());
    }
  else
    {
      mem.save(fout);
    }
  return 0;
}


/* ========================================
 * MAIN
 */


void
usage()
{
  fprintf(stderr,
          "Usage: gt1z [options] <fin> <fout>\n"
          "Compression tool for gt1 files\n"
          "Options:\n"
          " -c   Compress GT1 file <fin> into GT1Z file <fout> (default)\n"
          " -d   Decompress GT1Z file <fin> into GT1 file <fout>\n"
          " -v   Verify GT1Z file <fin> against GT1 file <fout>\n"
          " -f   Overwrites existing output file\n"
          " -r   Warn if the file is not relocatable\n"
          " -D   Increases verbosity level\n" );
  std::exit(10);
}

static void
check_filenames(std::string &fin, std::string &fout,
                const char *sin, const char *sout)
{
  int l_sin = std::strlen(sin);
  int l_sout = std::strlen(sout);
  if (fin.size() < l_sin || fin.substr(fin.size() - l_sin) != sin)
    info<0>("filename '%s' does not end with suffix '%s'", fin.c_str(), sin);
  else if (fout.empty())
    fout = fin.substr(0, fin.size() - l_sin) + sout;
  if (fout.empty())
    fout = fin + sout;
  else if (fout.size() < l_sout || fout.substr(fout.size() - l_sout) != sout)
    info<0>("filename '%s' does not end with suffix '%s'", fout.c_str(), sout);
}

static bool
file_exists(std::string filename)
{
  std::ifstream f(filename, std::ios_base::in | std::ios_base::binary);
  return f.good();
}

int
main(int argc, const char **argv)
{
  int mode = 0;
  int force = 0;
  int reloc = 0;
  std::string fin;
  std::string fout;
  /* Parse arguments */
  for (int i = 1; i < argc; i++) {
    if (argv[i][0] == '-')
      {
        for (const char *s = argv[i] + 1; *s; s++)
          switch (*s)
            {
            case 'c':
            case 'd':
            case 'v':
              if (mode)
                error("Conflicting options '-%c' and '-%c'", mode, *s);
              mode = *s;
              break;
            case 'f':
              force++;
              break;
            case 'D':
              verbose++;
              break;
            case 'r':
              reloc++;
              break;
            default:
              usage();
            }
      }
    else if (fin.empty())
      fin = argv[i];
    else if (fout.empty())
      fout = argv[i];
    else
      usage();
  }
  /* Process filenames */
  if (fin.empty())
    usage();
  if (mode == 0)
    mode = 'c';
  if (mode != 'c')
    check_filenames(fin, fout, ".gt1z", ".gt1");
  else
    check_filenames(fin, fout, ".gt1", ".gt1z");
  if (mode != 'v' && !force && file_exists(fout))
    error("not overwriting file '%s'", fout.c_str());
  relocatable = 1;
  if (mode != 'c')
    decompress(fin, fout, mode != 'd');
  else
    compress(fin, fout);
  if (reloc && !relocatable)
    info<0>("file '%s' is not relocatable",
            ((mode == 'c') ? fout : fin).c_str());
  return 0;
}

